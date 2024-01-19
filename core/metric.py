import tomllib
import cerberus
import datetime
import logging as log


from queue import Queue
from itertools import chain
from typing import List, Dict
from threading import Thread, Event

import core.config
import core.schemas.metrics_conf
import util.os


class Metric:
    def __init__(self, configDict):
        # Fall back to default sampling rate if none was specified
        if "sampling_rate" in configDict:
            self.sampling_rate = configDict["sampling_rate"]
        else:
            self.sampling_rate = core.config.Defaults.samplingRate

    def reset(self):
        pass

    def sample(self):
        pass

    def getResults(self):
        pass


class SysctlMetric(Metric):
    def __init__(self, configDict) -> None:
        super().__init__(configDict)
        self.values: Dict[str, List[int]] = {}
        self.oids = configDict["oids"]
        self.name = configDict["name"]

        for oid in self.oids:
            self.values[oid] = []

        log.debug(f"Registered sysctl metric group: '{self.name}'")

    def sample(self):
        for oid in self.oids:
            self.values[oid].append(util.os.sysctl(oid))
            log.debug(f"Sampled sysctl '{oid}'")

    def getResults(self, resultsDict):
        for oid in self.oids:
            resultsDict["sysctl"][oid] = self.values[oid].copy()

    def reset(self):
        for oid in self.oids:
            self.values[oid].clear()

    def getName(self):
        return "sysctl"


class PsMetric(Metric):
    supportedStats: List[str] = {
        "time",
    }

    def __init__(self, configDict) -> None:
        super().__init__(configDict)

        self.valueDict = {}
        self.cmd = configDict["command"]
        self.stats = configDict["stats"]

        for stat in self.stats:
            if stat not in PsMetric.supportedStats:
                raise ValueError(f"Sampling 'ps' stat '{stat}' is not supported yet")

            self.valueDict[stat] = []

        log.debug(
            f"Registered 'ps' metric for process '{self.cmd}' - tracking '{self.stats}'"
        )

    def sample(self) -> None:
        procDict = util.os.procInfo(self.cmd)
        if procDict:
            for stat in self.stats:
                match stat:
                    case "time":
                        cpuTimeTimestamp = datetime.datetime.strptime(
                            procDict["cpu-time"], "%M:%S.%f"
                        ).timestamp()
                        self.valueDict[stat].append(cpuTimeTimestamp)
            log.debug(f"Sampled ps metric for '{self.cmd}'")
        else:
            log.warn(f"Unable to fetch process info for '{self.cmd}'")

    def getResults(self, resultsDict) -> None:
        resultsDict["ps"][self.cmd] = {}

        for stat in self.stats:
            resultsDict["ps"][self.cmd][stat] = self.valueDict[stat].copy()

    def reset(self) -> None:
        for stat in self.stats:
            self.valueDict[stat].clear()

    def getName(self):
        return "ps"


class MetricRegistry:
    diffMetrics: List[Metric] = []
    continuousMetrics: Dict[int, Metric] = {}
    tq: list[(Thread, Event)] = []

    @staticmethod
    def loadMetrics(configPath: str) -> None:
        with open(configPath, mode="rb") as file:
            metricsConfig = tomllib.load(file)

        v = cerberus.Validator(core.schemas.metrics_conf.schema)
        if not v.validate(metricsConfig):
            raise ValueError(f"invalid metrics configuration file: {v.errors}")

        for metricClass, metricDicts in metricsConfig.items():
            ctor = None
            match metricClass:
                case "sysctl":
                    ctor = SysctlMetric
                case "ps":
                    ctor = PsMetric
                case "dtrace":
                    continue

            for metricDict in metricDicts:
                m = ctor(metricDict)
                if "sampling_rate" in metricDict:
                    sampling_rate = metricDict["sampling_rate"]
                    if sampling_rate not in MetricRegistry.continuousMetrics:
                        MetricRegistry.continuousMetrics[sampling_rate] = []
                    MetricRegistry.continuousMetrics[sampling_rate].append(m)
                else:
                    MetricRegistry.diffMetrics.append(m)

    @staticmethod
    def sampleDiffMetrics():
        for m in MetricRegistry.diffMetrics:
            m.sample()

    @staticmethod
    def startSamplingThreads():
        def samplingThread(
            metrics: List[Metric], samplingRateMs: int, stop: Event
        ) -> None:
            while not stop.wait(samplingRateMs / 1000.0):
                for m in metrics:
                    m.sample()

        # Create threads for monitoring sysctls
        if len(MetricRegistry.continuousMetrics) == 0:
            return

        MetricRegistry.tq.clear()
        for samplingRate, m in MetricRegistry.continuousMetrics.items():
            e = Event()
            t = Thread(
                target=samplingThread,
                args=(m, samplingRate, e),
            )
            MetricRegistry.tq.append((t, e))

            for t, _ in MetricRegistry.tq:
                t.start()

    @staticmethod
    def stopSamplingThreads():
        # Signal the monitoring threads to stop
        for _, e in MetricRegistry.tq:
            e.set()

        for t, _ in MetricRegistry.tq:
            t.join()

    @staticmethod
    def fetchResults():
        results = {"sysctl": {}, "ps": {}}
        for m in MetricRegistry.diffMetrics:
            m.getResults(results)
            m.reset()

        for metricsList in MetricRegistry.continuousMetrics.values():
            for m in metricsList:
                m.getResults(results)
                m.reset()

        return results


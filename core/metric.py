import tomllib
import cerberus
import logging as log

from typing import List

import core.schemas.metrics_conf
import util.os

from util.structs import DictObj


class Metric:
    def __init__(self):
        self.values: List[int] = list()

    def reset(self):
        self.values.clear()

    def sample(self):
        pass


class SysctlMetric(Metric):
    def __init__(self, configDict) -> None:
        super().__init__()
        self.config = DictObj(**configDict)
        log.debug(f"Registered sysctl metric: '{self.config.oid}'")

    def sample(self):
        self.values.append(util.os.sysctl(self.config.oid))
        log.debug(f"Sampled sysctl '{self.config.oid}'")


class MetricRegistry:
    sysctls: List[SysctlMetric]

    @staticmethod
    def loadMetrics(configPath: str) -> None:
        with open(configPath, mode="rb") as file:
            metricsConfig = tomllib.load(file)

        v = cerberus.Validator(core.schemas.metrics_conf.schema)
        if not v.validate(metricsConfig):
            raise ValueError(f"invalid metrics configuration file: {v.errors}")

        MetricRegistry.sysctls = [SysctlMetric(x) for x in metricsConfig["sysctl"]]

    @staticmethod
    def getSysctls(mode: str) -> List[SysctlMetric]:
        return [x for x in MetricRegistry.sysctls if x.config.mode == mode]

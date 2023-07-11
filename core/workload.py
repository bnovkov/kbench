import os
import sys
import glob
import tomllib
import cerberus
import logging as log

from multiprocessing import Process, Semaphore
from queue import Queue
from threading import Thread, Event
from typing import Dict, Set, List
from itertools import chain

from core.benchmark import BenchmarkRegistry, BenchmarkBase
from core.metric import MetricRegistry, SysctlMetric

import util.os
import util.runners as runners
import core.schemas.workload_conf

from util.structs import DictObj


class Workload:
    def __init__(self, configPath: str) -> None:
        with open(configPath, mode="rb") as file:
            config = tomllib.load(file)

        v = cerberus.Validator(core.schemas.workload_conf.schema)

        if not v.validate(config):
            raise ValueError(f"invalid workload configuration: {v.errors}")

        config = v.normalized(config)

        self.config = DictObj(**config["info"])
        self.name = self.config.name
        self.benchmark = self.config.benchmark
        self.run_args = self.config.run_args
        self.iterations = self.config.iterations


class WorkloadRegistry:
    workloads: Dict[str, Workload] = dict()
    targetBenchmarks: Set[BenchmarkBase] = set()

    @staticmethod
    def loadWorkloads(workloadDirPath: str) -> None:
        loadedBenchmarks = BenchmarkRegistry.getLoadedBenchmarkNames()

        for file in glob.glob(os.path.join(workloadDirPath, "*.toml")):
            w = Workload(file)

            # Check if benchmark specified by workload exists
            if w.benchmark not in loadedBenchmarks:
                raise ValueError(
                    f"Workload {w.name} specified non-existent benchmark {w.benchmark}"
                )

            WorkloadRegistry.workloads[w.name] = w
            WorkloadRegistry.targetBenchmarks.add(w.benchmark)

            log.info(f"Registered '{w.name}' workload")

    @staticmethod
    def runWorkloads() -> Dict:
        cwd = os.getcwd()
        func = None
        sema = Semaphore(1)
        tq: list[(Thread, Event)] = []

        ncpu = util.os.sysctl("hw.ncpu")
        log.debug(f"Number of CPUs: {ncpu}")

        def pausedProc(target, sema, args, kwargs):
            sema.acquire()
            f = open(os.devnull, "w")
            sys.stdout = f
            target(*args, **kwargs)
            sema.release()

        def samplingThread(
            sysctls: List[SysctlMetric], samplingRateMs: int, stop: Event
        ) -> None:
            while not stop.wait(samplingRateMs / 1000.0):
                for s in sysctls:
                    s.sample()

        results = {}

        for name, w in WorkloadRegistry.workloads.items():
            benchmark = BenchmarkRegistry.registry[w.benchmark]
            diffSysctls = MetricRegistry.getSysctls("diff")
            monitorSysctls = MetricRegistry.getSysctls("monitor")
            monitorSysctlsGrouped = {}
            runResults = {"sysctl": {}, "dtrace": {}}

            for s in monitorSysctls:
                if s.config.sampling_rate not in monitorSysctlsGrouped:
                    monitorSysctlsGrouped[s.config.sampling_rate] = []

                monitorSysctlsGrouped[s.config.sampling_rate].append(s)
            for i in range(0, w.iterations):
                tq.clear()

                # Select and execute specified runner
                match benchmark.run.runner:
                    case "py":
                        benchmark.preRun()
                        process = Process(
                            target=pausedProc,
                            args=(benchmark.run, sema, [w.run_args], {}),
                        )
                    case "make":
                        process = Process(
                            target=pausedProc,
                            args=(
                                runners.make,
                                sema,
                                [w.run_args],
                                {
                                    "ncpu": ncpu,
                                    "envvar": benchmark.run.env,
                                    "rootdir": benchmark.files.rootdir,
                                    "silent": True,
                                },
                            ),
                        )
                    case _:
                        raise ValueError(
                            f"Invalid benchmark runner specified for '{benchmark.name}'"
                        )

                log.info(f"Running '{w.name}', run #{i+1}")

                sema.acquire()
                process.start()

                # Sample sysctl before we start the process
                for sysctl in diffSysctls:
                    sysctl.sample()

                # Create threads for monitoring sysctls
                if len(monitorSysctlsGrouped) != 0:
                    for k, v in monitorSysctlsGrouped.items():
                        e = Event()
                        t = Thread(
                            target=samplingThread,
                            args=(v, v[0].config.sampling_rate, e),
                        )
                        tq.append((t, e))

                    for t, _ in tq:
                        t.start()

                sema.release()

                process.join()

                # Signal the monitoring threads to stop
                if len(monitorSysctlsGrouped) != 0:
                    for _, e in tq:
                        e.set()

                    for t, _ in tq:
                        t.join()

                # Sample sysctl after the process finished
                for sysctl in diffSysctls:
                    sysctl.sample()

                # Save results
                for sysctl in list(chain(diffSysctls, monitorSysctls)):
                    if sysctl.config.oid not in runResults["sysctl"]:
                        runResults["sysctl"][sysctl.config.oid] = []
                    runResults["sysctl"][sysctl.config.oid] += sysctl.values.copy()

                    sysctl.reset()

        results[w.name] = runResults

        return results

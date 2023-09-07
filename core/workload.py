import os
import sys
import glob
import time
import tomllib
import cerberus
import logging as log

from multiprocessing import Process, Semaphore
from typing import Dict, Set, List

from core.benchmark import BenchmarkRegistry, BenchmarkBase
from core.metric import MetricRegistry, SysctlMetric

import util.os
import util.runners as runners
import core.schemas.workload_conf


class Workload:
    def __init__(self, configPath: str) -> None:
        with open(configPath, mode="rb") as file:
            config = tomllib.load(file)

        v = cerberus.Validator(core.schemas.workload_conf.schema)
        if not v.validate(config):
            raise ValueError(f"invalid workload configuration: {v.errors}")
        config = v.normalized(config)

        self.name = config["info"]["name"]
        self.benchmark = config["info"]["benchmark"]
        self.run_args = config["info"]["run_args"]
        self.iterations = config["info"].get("iterations", 1)


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

        ncpu = util.os.sysctl("hw.ncpu")
        log.debug(f"Number of CPUs: {ncpu}")

        def pausedProc(runner, sema, args, kwargs):
            sema.acquire()
            f = open(os.devnull, "w")
            sys.stdout = f
            runner.run(*args, silent=True)
            sema.release()

        results = {}

        for name, w in WorkloadRegistry.workloads.items():
            benchmark = BenchmarkRegistry.registry[w.benchmark]
            runResults = {}

            for i in range(0, w.iterations):
                runResults[i] = {}

                benchmark.preRun()
                process = Process(
                    target=pausedProc,
                    args=(benchmark.runner, sema, [w.run_args], {}),
                )

                log.info(f"Running '{w.name}', run #{i+1}")

                sema.acquire()
                process.start()

                MetricRegistry.startSamplingThreads()
                # Sample diffs before we start the process
                MetricRegistry.sampleDiffMetrics()

                startTs = time.perf_counter()
                sema.release()

                process.join()
                endTs = time.perf_counter()
                runResults[i]["time"] = endTs - startTs

                MetricRegistry.stopSamplingThreads()
                # Sample diffs after the process finished
                MetricRegistry.sampleDiffMetrics()

                # Save results
                runResults[i]["metrics"] = MetricRegistry.fetchResults()

        results[w.name] = runResults

        return results

import os
import json
import argparse
import coloredlogs
import logging as log

from datetime import datetime

from core.benchmark import BenchmarkRegistry
from core.workload import WorkloadRegistry
from core.metric import MetricRegistry

from core.config import RunConfig

coloredlogs.install(level="INFO")

parser = argparse.ArgumentParser()
requiredArgs = parser.add_argument_group("required arguments")
requiredArgs.add_argument(
    "-a", "--action", choices=["build", "run", "clean"], help="action", required=True
)

parser.add_argument(
    "-c", "--config", type=str, help="configuration file for benchmark run"
)
parser.add_argument("-v", "--verbose", action="store_true", help="increase verbosity")

args = parser.parse_args()

if args.verbose:
    coloredlogs.install(level="DEBUG")

try:
    config = RunConfig(args)

    # Load all benchmarks and register them
    BenchmarkRegistry.loadBenchmarks("./benchmarks")
    WorkloadRegistry.loadWorkloads("./workloads")

    match config.action:
        case "build":
            BenchmarkRegistry.buildBenchmarks()
        case "run":
            t = datetime.now()
            configName = os.path.splitext(os.path.basename(config.configPath))[0]
            resultFilename = f"{configName}-{t.strftime('%d%m%Y-%H%M')}.json"
            # Load specified metrics
            MetricRegistry.loadMetrics(config.metricsPath)
            BenchmarkRegistry.buildBenchmarks(WorkloadRegistry.targetBenchmarks)
            results = WorkloadRegistry.runWorkloads()

            # Add metadata
            results["uname"] = os.uname().version

            with open(os.path.join("./results", resultFilename), "w") as file:
                json.dump(results, file)
            log.info("Wrote benchmarking results to '%s'", resultFilename)


except Exception as e:
    log.exception(e, exc_info=True)
    exit(-1)

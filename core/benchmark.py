import os
import imp
import glob
import tomllib
import cerberus
import logging as log

from typing import Set, Dict
from jinja2 import Template

import core
import core.setup as setup
from core import runners


class BenchmarkBase:
    def initSetupInfo(self) -> None:
        self.setup = None

    #        if "setup" in self.config:
    #            self.setup = DictObj(**self.config["setup"])

    def __init__(self, cwd) -> None:
        cwd = os.path.abspath(cwd)

        # Process the configuration file
        config = None
        with open(os.path.join(cwd, "config.toml")) as file:
            config = tomllib.loads(file.read())

        v = cerberus.Validator(core.schemas.bench_conf.schema)
        if not v.validate(config):
            raise ValueError(f"invalid benchmark configuration: {v.errors}")

        # Populate basic benchmark info
        self.path = cwd
        self.name = config["info"]["name"]
        self.desc = config["info"]["description"]

        # Process runner block
        match config["run"]:
            case {"make": _}:
                self.runner = runners.MakeRunner(config["run"]["make"], cwd)
            case _:
                raise ValueError(f"'{self.name}': Unknown runner {runnerId} specified")

        # Add handler for fetching source files, if needed
        self.fileHandler = None
        match config["files"]:
            case {"fetch": {"filename": fname, "url": url}}:
                self.fileHandler = setup.FetchSetupHandler(
                    os.path.join(cwd, fname), url
                )

            # TODO: point for adding future file handlers

        if self.fileHandler == None:
            raise ValueError(f"'{self.name}': No setup procedure was specified")

        log.info("Loaded benchmark info for '%s'", self.name)

    def preRun(self):
        pass

    def postRun(self):
        pass

    # For every class that inherits from the current,
    # the class name will be added to plugins
    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        inst = cls()
        BenchmarkRegistry.registry[inst.name] = inst


class BenchmarkRegistry:
    registry: Dict[str, BenchmarkBase] = dict()

    @staticmethod
    def loadBenchmarks(benchmarkDir):
        insts = list()

        for path in glob.glob(os.path.join(benchmarkDir, "*/*")):
            modname, ext = os.path.splitext(os.path.basename(path))
            if ext == ".py":
                file, path, descr = imp.find_module(modname, [os.path.dirname(path)])
                if file:
                    imp.load_module(modname, file, path, descr)

    @staticmethod
    def getLoadedBenchmarkNames() -> Set[str]:
        return set(BenchmarkRegistry.registry.keys())

    @staticmethod
    def buildBenchmarks(benchmarkSet=None):
        oldcwd = os.getcwd()
        for benchmark in BenchmarkRegistry.registry.values():
            if benchmarkSet and benchmark.name not in benchmarkSet:
                continue
            os.chdir(benchmark.path)

            # Setup source files, if neccessary
            if benchmark.fileHandler:
                benchmark.fileHandler.run()

            # Run the runner's setup
            benchmark.runner.setup()

        os.chdir(oldcwd)

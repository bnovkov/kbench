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
from util.os import pushd


class BenchmarkBase:
    def initSetupInfo(self) -> None:
        self.setup = None

    #        if "setup" in self.config:
    #            self.setup = DictObj(**self.config["setup"])

    def __init__(self, cwd) -> None:
        cwd = os.path.abspath(cwd)
        log.debug(f"Processing {cwd}")
        # Process the configuration file
        config = None
        with open(os.path.join(cwd, "config.toml")) as file:
            config = tomllib.loads(file.read())

        v = cerberus.Validator(core.schemas.bench_conf.schema)
        if not v.validate(config):
            raise ValueError(f"{cwd}: invalid benchmark configuration: {v.errors}")
        config = v.normalized(config)
        print(config)
        # Populate basic benchmark info
        self.path = cwd
        self.name = config["info"]["name"]
        self.desc = config["info"]["description"]
        self.prebuilt = config["info"]["prebuilt"]

        # Process runner block
        match config["run"]:
            case {"make": _}:
                self.runner = runners.MakeRunner(config["run"]["make"], cwd)
            case {"exec": _}:
                self.runner = runners.ExecRunner(config["run"]["exec"], cwd)
            case _:
                raise ValueError(f"'{self.name}': Unknown runner {config['run']} specified")

        if not self.prebuilt:
            # Add handler for fetching source files, if needed
            self.srcFileHandler = None
            match config["src"]:
                case {"fetch": {"url": url}}:
                    self.srcFileHandler = setup.FetchSrcHandler(url, cwd)
                case {"git": {"url": url}}:
                    self.srcFileHandler = setup.GitSrcHandler(url, cwd)

            if self.srcFileHandler == None:
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
        for benchmark in BenchmarkRegistry.registry.values():
            if benchmarkSet and benchmark.name not in benchmarkSet:
                continue
            with pushd(benchmark.path):
                # Setup source files, if neccessary
                if not benchmark.prebuilt and benchmark.srcFileHandler:
                    if not os.path.isdir("./src"):
                        os.mkdir("./src")
                    if len(os.listdir("./src")) == 0:
                        log.info("Fetching source files for '%s'", benchmark.name)
                        benchmark.srcFileHandler.run()

                # Run the runner's setup
                benchmark.runner.setup()


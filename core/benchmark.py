import os
import imp
import glob
import tomllib
import cerberus
import shutil
import logging as log

from typing import Set, Dict

import core.setup as setup
from core.config import BenchConfig

from util.structs import DictObj


class FilesInfo:
    def __init__(self, cwd, filesConfigBlock) -> None:
        self.fileHandler = None
        self.rootdir = os.path.join(cwd, filesConfigBlock["rootdir"])

        match filesConfigBlock:
            case {"fetch": {"filename": fname, "url": url}}:
                self.fileHandler = setup.FetchSetupHandler(
                    os.path.join(cwd, fname), url
                )


class BenchmarkBase:
    # Install appropriate handlers for fetching source files, if any
    def initFileInfo(self, cwd) -> None:
        self.files = None

        if "files" in self.config:
            self.files = FilesInfo(cwd, self.config["files"])

    def initRunInfo(self) -> None:
        self.run = DictObj(**self.config["run"])

    def initSetupInfo(self) -> None:
        self.setup = None

        if "setup" in self.config:
            self.setup = DictObj(**self.config["setup"])

    def __init__(self, cwd) -> None:
        cwd = os.path.abspath(cwd)

        self.config = BenchConfig(cwd)
        self.name = self.config["info"]["name"]
        self.path = cwd

        self.initFileInfo(cwd)
        self.initRunInfo()
        self.initSetupInfo()

        log.info("Loaded benchmark info for '%s'", self.name)

    def getConfig(self) -> BenchConfig:
        return self.config

    def setupFiles(self) -> None:
        if self.files:
            self.files.fileHandler.run()
            log.info(f"Unpacking file '{self.files.fileHandler.path}'")

            shutil.unpack_archive(self.files.fileHandler.path, self.path)

    def preRun(self):
        pass

    def runBenchmark(self):
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

            # Setup source files, if neccessary
            if benchmark.files:
                if (
                    os.path.isdir(benchmark.files.rootdir)
                    and len(os.listdir(benchmark.files.rootdir)) != 0
                ):
                    log.info(
                        f"'{benchmark.name}': Source files already present - skipping setup"
                    )
                else:
                    benchmark.setupFiles()

            runConfig = benchmark.config["run"]
            tmpdir = runConfig["tmpfiledir"]

            if not os.path.isdir(tmpdir):
                log.info(f"'{benchmark.name}': creating build directory '{tmpdir}'")
                os.makedirs(tmpdir)

            if benchmark.setup:
                if len(os.listdir(benchmark.setup.builddir)) != 0:
                    log.info(
                        f"'{benchmark.name}': build directory not empty - skipping build"
                    )

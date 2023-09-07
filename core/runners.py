import os
import shutil
import subprocess
import logging as log


class MakeRunner:
    def __init__(self, makeConfig, cwd):
        self.rootdir = os.path.join(cwd, makeConfig["rootdir"])
        self.ncpu = makeConfig.get("ncpu", 1)
        self.envvar = makeConfig.get("env")
        self.builddir = None
        if "builddir" in makeConfig:
            self.builddir = os.path.join(cwd, makeConfig["builddir"])

    def setup(self):
        if not os.path.isdir(self.builddir):
            log.info(f"Creating build directory '{self.builddir}'")
            os.makedirs(self.builddir)

    def run(self, *args, silent=False):
        log.debug("env: %s, rootdir: %s", str(self.envvar), str(self.rootdir))
        if self.rootdir:
            os.chdir(self.rootdir)

        stdout = None
        if silent:
            stdout = subprocess.DEVNULL

        subprocess.run(
            ["make", f"-j{self.ncpu}", *args], env=self.envvar, stdout=stdout
        )

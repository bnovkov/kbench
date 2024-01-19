import os
import shutil
import subprocess
import logging as log

from core.config import SysInfo
from util.os import pushd

class MakeRunner:
    def __init__(self, makeConfig, cwd):
        self.rootdir = os.path.join(cwd, "src", makeConfig["rootdir"])
        self.ncpu = makeConfig.get("ncpu", SysInfo.ncpu)
        self.envvar = makeConfig.get("env")
        self.builddir = None
        if "builddir" in makeConfig:
            self.builddir = os.path.join(cwd, makeConfig["builddir"])

    def setup(self):
        if self.builddir and not os.path.isdir(self.builddir):
            log.info(f"Creating build directory '{self.builddir}'")
            os.makedirs(self.builddir)

    def run(self, args, silent=False):
        log.debug("env: %s, rootdir: %s", str(self.envvar), str(self.rootdir))
        if self.rootdir:
            os.chdir(self.rootdir)

        stdout = None
        if silent:
            stdout = subprocess.DEVNULL

        subprocess.run(
            ["make", f"-j{self.ncpu}", *args], env=self.envvar, stdout=stdout
        )

class ExecRunner:
    def __init__(self, execConfig, cwd):
        self.cmds = execConfig.get("cmds", [])
        self.envvar = execConfig.get("env", {})
        self.cwd = cwd

    def setup(self):
        for cmd in self.cmds:
            if not os.path.exists(cmd):
                raise Exception(f"cannot find benchmark binary {cmd}")

    def run(self, args, silent=False):
        if args[0] not in self.cmds:
            raise Exception("exec: executable {} is not a part of the benchmark".format(args[0]))
        stdout = None
        if silent:
            stdout = subprocess.DEVNULL
        args[0] = os.path.join(self.cwd, args[0])
        with pushd(self.cwd):
            log.debug("exec: cwd: %s env: %s, args: %s", os.getcwd(), str(self.envvar), args)
            subprocess.run(
                args, env=self.envvar, stdout=stdout
            )

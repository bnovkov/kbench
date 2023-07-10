import os

import core.benchmark
import util.runners as runners


class FbsdBuild(core.benchmark.BenchmarkBase):
    def __init__(self):
        super().__init__("benchmarks/fbsd-build")

    def preRun(self):
        os.chdir(os.path.join(self.filesInfo.fileDirPath, "usr/src"))

    def run(self, args):
        env = {"MAKEOBJDIRPREFIX": self.builddir}
        runners.make(args, envvar=env)

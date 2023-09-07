import core.benchmark


class FbsdBuild(core.benchmark.BenchmarkBase):
    def __init__(self):
        super().__init__("benchmarks/fbsd-build")

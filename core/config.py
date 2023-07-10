import os
import tomllib
import logging as log
import cerberus

from jinja2 import Template

import core.schemas.bench_conf
import core.schemas.run_conf

from util.structs import DictObj, DummyDict, ConfigDummyDict


class RunConfig:
    defaultConfigPath = "config/default.toml"

    def __init__(self, args):
        self.action = args.action

        self.configPath = args.config
        if not self.configPath:
            self.configPath = RunConfig.defaultConfigPath
            log.info("Configuration file not specified - falling back to default.toml")

        with open(self.configPath, mode="rb") as file:
            self.config = tomllib.load(file)

        self.validateConfig()
        self.config = DictObj(**self.config)

        self.metricsPath = self.config.metrics
        self.benchmarkSet = None
        if self.config.benchmarks != "all":
            self.benchmarkSet = set(self.config.benchmarks)

    def validateConfig(self):
        v = cerberus.Validator(core.schemas.run_conf.schema)
        if not v.validate(self.config):
            raise ValueError(f"invalid benchmark configuration: {v.errors}")


class BenchConfig:
    def validateConfig(self):
        v = cerberus.Validator(core.schemas.bench_conf.schema)
        if not v.validate(self.config):
            raise ValueError(f"invalid benchmark configuration: {v.errors}")

    def __contains__(self, key):
        return key in self.config

    def __getitem__(self, key):
        return self.config[key]

    def normalizePaths(self, cwd):
        if "tmpfiledir" in self.config["run"]:
            self.config["run"]["tmpfiledir"] = os.path.join(
                cwd, self.config["run"]["tmpfiledir"]
            )

    def __init__(self, cwd):
        template = None
        with open(os.path.join(cwd, "config.toml")) as file:
            template = Template(file.read())

        # First run, replace all jinja placeholders with empty strings
        tomlNoPlaceholders = template.render(bench=ConfigDummyDict())
        self.config = tomllib.loads(tomlNoPlaceholders)
        self.normalizePaths(cwd)

        # Second run, render the template with the previously loaded non-templatable values
        renderedToml = template.render(bench=self.config)
        self.config = tomllib.loads(renderedToml)
        self.validateConfig()

        self.normalizePaths(cwd)

        self.filesInfo = None

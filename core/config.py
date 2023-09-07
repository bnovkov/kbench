import os
import tomllib
import logging as log
import cerberus

import core.schemas.bench_conf
import core.schemas.run_conf


class Defaults:
    samplingRate = 1000


class RunConfig:
    defaultConfigPath = "config/default.toml"

    def __init__(self, args):
        self.action = args.action

        self.configPath = args.config
        if not self.configPath:
            self.configPath = RunConfig.defaultConfigPath
            log.info("Configuration file not specified - falling back to default.toml")

        with open(self.configPath, mode="rb") as file:
            config = tomllib.load(file)

        self.validateConfig(config)

        self.metricsPath = config["metrics"]
        self.benchmarkSet = None
        if config["benchmarks"] != "all":
            self.benchmarkSet = set(config["benchmarks"])

    def validateConfig(self, config):
        v = cerberus.Validator(core.schemas.run_conf.schema)
        if not v.validate(config):
            raise ValueError(f"invalid benchmark configuration: {v.errors}")

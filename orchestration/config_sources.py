"""Pipeline configuration sources"""

import logging

logger = logging.getLogger("orchestration.config_sources")


class ConfigSource:
    """Base config source"""

    def load(self) -> dict:
        raise NotImplementedError


class DictSource(ConfigSource):
    """Dictionary config source"""

    def __init__(self, config: dict):
        self.config = config

    def load(self) -> dict:
        return self.config


class MultiSource(ConfigSource):
    """Multiple config sources"""

    def __init__(self, sources: list[ConfigSource]):
        self.sources = sources

    def load(self) -> dict:
        result = {}
        for source in self.sources:
            result.update(source.load())
        return result


def merge_configs(*configs: dict) -> dict:
    """Merge multiple configs"""
    result = {}
    for config in configs:
        result.update(config)
    return result

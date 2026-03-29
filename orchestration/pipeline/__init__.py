"""Pipeline module"""

from orchestration.pipeline.core import Pipeline


# Placeholder for backward compatibility
class ConversionPipeline:
    def __init__(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        return {}

__all__ = ["Pipeline", "ConversionPipeline"]

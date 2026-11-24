"""Pipeline module"""

from orchestration.pipeline.core import Pipeline
from orchestration.pipeline.pipeline import run_pipeline


# Placeholder for backward compatibility
class ConversionPipeline:
    def __init__(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        return {}

__all__ = ["Pipeline", "ConversionPipeline", "run_pipeline"]

"""Pipeline phase plugins"""

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

logger = logging.getLogger("orchestration.phase_plugins")


class PhaseType(StrEnum):
    """Phase types"""
    ANALYZE = "analyze"
    DATABASE = "database"
    HASKELL = "haskell"
    QML = "qml"
    REPORTS = "reports"


@dataclass
class PhaseResult:
    """Phase execution result"""
    success: bool
    files_processed: int = 0
    output: dict[str, Any] = None
    errors: list[str] = None

    def __post_init__(self):
        if self.output is None:
            self.output = {}
        if self.errors is None:
            self.errors = []


class PhasePlugin:
    """Base phase plugin"""

    name: str = ""
    phase_type: PhaseType = PhaseType.ANALYZE

    def before(self, context: dict) -> dict:
        """Before phase execution"""
        return context

    def execute(self, context: dict) -> PhaseResult:
        """Execute phase"""
        raise NotImplementedError

    def after(self, context: dict, result: PhaseResult):
        """After phase execution"""
        pass


class AnalyzePhasePlugin(PhasePlugin):
    """Custom analyze phase"""
    name = "custom_analyze"
    phase_type = PhaseType.ANALYZE

    def execute(self, context: dict) -> PhaseResult:
        # Custom analysis logic
        return PhaseResult(success=True, files_processed=0)


class DatabasePhasePlugin(PhasePlugin):
    """Custom database phase"""
    name = "custom_database"
    phase_type = PhaseType.DATABASE

    def execute(self, context: dict) -> PhaseResult:
        return PhaseResult(success=True, files_processed=0)


class PhasePluginManager:
    """Manage phase plugins"""

    def __init__(self):
        self.plugins: dict[PhaseType, list[PhasePlugin]] = {
            phase: [] for phase in PhaseType
        }

    def register(self, plugin: PhasePlugin):
        """Register plugin"""
        self.plugins[plugin.phase_type].append(plugin)
        logger.info(f"Registered plugin: {plugin.name}")

    def get_plugins(self, phase_type: PhaseType) -> list[PhasePlugin]:
        """Get plugins for phase"""
        return self.plugins.get(phase_type, [])

    async def execute_phase(
        self,
        phase_type: PhaseType,
        context: dict,
    ) -> PhaseResult:
        """Execute phase with plugins"""
        plugins = self.get_plugins(phase_type)

        if not plugins:
            return PhaseResult(success=True)

        # Run before hooks
        for plugin in plugins:
            context = plugin.before(context)

        # Execute first plugin
        result = plugins[0].execute(context)

        # Run after hooks
        for plugin in plugins:
            plugin.after(context, result)

        return result


# Global manager
_plugin_manager: PhasePluginManager | None = None


def get_plugin_manager() -> PhasePluginManager:
    """Get plugin manager"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PhasePluginManager()
    return _plugin_manager

"""Pipeline hooks for extensibility"""

import os
import logging
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("orchestration.hooks")


class HookPhase(Enum):
    """Pipeline phases for hooks"""
    BEFORE_RUN = "before_run"
    AFTER_RUN = "after_run"
    BEFORE_PHASE = "before_phase"
    AFTER_PHASE = "after_phase"
    ON_FILE = "on_file"
    ON_ERROR = "on_error"
    ON_COMPLETE = "on_complete"


@dataclass
class Hook:
    """Hook definition"""
    name: str
    phase: HookPhase
    callback: Callable
    description: str = ""
    enabled: bool = True


@dataclass
class HookContext:
    """Context passed to hooks"""
    phase: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class HookManager:
    """Manage pipeline hooks"""
    
    def __init__(self):
        self.hooks: Dict[HookPhase, List[Hook]] = {
            phase: [] for phase in HookPhase
        }
        self._register_builtin_hooks()
    
    def _register_builtin_hooks(self):
        """Register built-in hooks"""
        # Logging hook
        self.register_hook(Hook(
            name="log",
            phase=HookPhase.AFTER_PHASE,
            callback=self._log_hook,
            description="Log phase completion",
        ))
    
    def register_hook(self, hook: Hook):
        """Register a hook"""
        self.hooks[hook.phase].append(hook)
        logger.info(f"Registered hook: {hook.name} for {hook.phase.value}")
    
    def unregister_hook(self, name: str):
        """Unregister a hook"""
        for phase_hooks in self.hooks.values():
            phase_hooks[:] = [h for h in phase_hooks if h.name != name]
    
    async def trigger(self, phase: HookPhase, context: HookContext) -> List[Any]:
        """Trigger hooks for a phase"""
        results = []
        
        for hook in self.hooks.get(phase, []):
            if not hook.enabled:
                continue
            
            try:
                result = hook.callback(context)
                
                # Handle coroutines
                if hasattr(result, '__await__'):
                    result = await result
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Hook {hook.name} failed: {e}")
        
        return results
    
    def _log_hook(self, context: HookContext) -> None:
        """Built-in logging hook"""
        logger.info(f"Phase {context.phase}: {context.data}")
    
    def register_callback(
        self,
        name: str,
        phase: HookPhase,
        callback: Callable,
        description: str = "",
    ):
        """Convenience method to register a callback"""
        hook = Hook(
            name=name,
            phase=phase,
            callback=callback,
            description=description,
        )
        self.register_hook(hook)
    
    def list_hooks(self) -> List[Dict[str, Any]]:
        """List all registered hooks"""
        return [
            {
                "name": h.name,
                "phase": h.phase.value,
                "description": h.description,
                "enabled": h.enabled,
            }
            for phase_hooks in self.hooks.values()
            for h in phase_hooks
        ]


class PipelineHookMixin:
    """Mixin to add hooks to pipeline"""
    
    def __init__(self):
        self.hook_manager = HookManager()
    
    async def _run_hooks(self, phase: HookPhase, **kwargs):
        """Run hooks for a phase"""
        context = HookContext(
            phase=kwargs.get("phase", "unknown"),
            data=kwargs,
        )
        
        return await self.hook_manager.trigger(phase, context)
    
    def add_hook(self, name: str, phase: HookPhase, callback: Callable):
        """Add a hook to pipeline"""
        self.hook_manager.register_callback(name, phase, callback)


# Built-in hook examples
def log_phase_hook(context: HookContext):
    """Log phase information"""
    phase = context.data.get("phase", "unknown")
    duration = context.data.get("duration", 0)
    files = context.data.get("files", 0)
    
    logger.info(f"Phase '{phase}' completed in {duration:.1f}s, {files} files")


def notify_hook(context: HookContext):
    """Send notification on completion"""
    # This would integrate with notifications
    phase = context.data.get("phase")
    logger.info(f"Notification: {phase} completed")


def metrics_hook(context: HookContext):
    """Record metrics"""
    # This would update metrics
    pass


def validate_hook(context: HookContext):
    """Validate output"""
    # This would run validation
    pass


# Global hook manager
_hook_manager: Optional[HookManager] = None


def get_hook_manager() -> HookManager:
    """Get global hook manager"""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = HookManager()
    return _hook_manager

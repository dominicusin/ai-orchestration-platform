"""Pipeline circuit states"""

import logging
from typing import Dict, Any
from enum import Enum

logger = logging.getLogger("orchestration.circuit_states")


class State(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitStateMachine:
    """Circuit state machine"""
    
    def __init__(self):
        self.state = State.CLOSED
        self.failures = 0
        self.successes = 0
    
    def record_success(self):
        self.failures = 0
        if self.state == State.HALF_OPEN:
            self.state = State.CLOSED
        self.successes += 1
    
    def record_failure(self):
        self.failures += 1
        if self.failures >= 5:
            self.state = State.OPEN
    
    def attempt_reset(self):
        if self.state == State.OPEN:
            self.state = State.HALF_OPEN
    
    def can_execute(self) -> bool:
        return self.state != State.OPEN

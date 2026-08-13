"""Run limits (docs/13-Agents/AgentFramework.md §3, AgentSecurity.md §1.5).

Step/loop/cost/time caps bound autonomy so a planner cannot run away. The runtime consults the
counter before each step and fails the run with a clear reason when a cap is hit.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RunLimits:
    max_steps: int = 12
    max_tool_calls: int = 12
    max_cost: int = 50
    max_wall_seconds: float = 30.0


@dataclass(slots=True)
class LimitCounter:
    limits: RunLimits
    clock: Callable[[], float] = time.monotonic
    steps: int = 0
    tool_calls: int = 0
    cost: int = 0
    _start: float = field(default=0.0)

    def start(self) -> None:
        self._start = self.clock()

    def exceeded(self) -> str | None:
        """Return a reason string if any limit is exceeded, else None."""
        if self.steps >= self.limits.max_steps:
            return f"step limit reached ({self.limits.max_steps})"
        if self.tool_calls >= self.limits.max_tool_calls:
            return f"tool-call limit reached ({self.limits.max_tool_calls})"
        if self.cost >= self.limits.max_cost:
            return f"cost budget reached ({self.limits.max_cost})"
        if self.clock() - self._start > self.limits.max_wall_seconds:
            return f"time limit reached ({self.limits.max_wall_seconds}s)"
        return None

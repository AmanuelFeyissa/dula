"""Per-provider call metrics for the LLM Gateway (docs/16-Operations/Observability.md).

Wraps an ``LLMProvider`` so every ``generate`` records ``ai_call_total`` /
``ai_call_errors_total`` / ``ai_call_duration_seconds`` under a *role* label -- ``production``
or ``candidate`` -- rather than the raw provider name. Wrapping the production and candidate
providers separately, *before* ``CanaryProvider`` composes them, is what makes the role exact
even on the error path (where no ``Usage.routed_provider`` comes back).
"""

from __future__ import annotations

import time

from dula_common.metrics import AI_CALL_DURATION, AI_CALL_ERRORS, AI_CALLS

from dula_ai.providers import LLMProvider
from dula_ai.types import Usage


class MeteredProvider:
    def __init__(self, inner: LLMProvider, *, service: str, role: str) -> None:
        self._inner = inner
        self._service = service
        self._role = role
        self.name = inner.name

    async def generate(self, system: str, user: str, *, max_tokens: int) -> tuple[str, Usage]:
        AI_CALLS.labels(self._service, self._role).inc()
        started = time.perf_counter()
        try:
            return await self._inner.generate(system, user, max_tokens=max_tokens)
        except Exception:
            AI_CALL_ERRORS.labels(self._service, self._role).inc()
            raise
        finally:
            AI_CALL_DURATION.labels(self._service, self._role).observe(
                time.perf_counter() - started
            )

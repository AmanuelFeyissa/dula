"""Telemetry hook (docs/16-Operations/Observability.md).

Phase 01 provides the integration seam only. The OpenTelemetry exporter + auto-
instrumentation (Prometheus/Grafana/Loki/Tempo) are wired in a later phase; this keeps a
single call site so adding it does not touch service code.
"""

from __future__ import annotations

import logging

_log = logging.getLogger(__name__)


def setup_telemetry(service_name: str) -> None:
    """Placeholder telemetry setup.

    Intentionally a no-op in Phase 01 (no OpenTelemetry dependency yet). Replaced with
    real OTel wiring later without changing callers.
    """
    _log.info("telemetry setup (stub)", extra={"service": service_name})

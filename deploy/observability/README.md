# Observability as-code (Phase 09)

Prometheus rules and a Grafana dashboard for the Dula platform, aligned with the OTel + Prometheus
+ Grafana + Loki + Tempo stack (docs/01-Project/TechnologyStack.md, docs/16-Operations).

| File | Purpose |
|------|---------|
| [prometheus-rules.yaml](./prometheus-rules.yaml) | `PrometheusRule` — recording rules + SLO/infra/MLOps alerts. Infra-signal alerts (target down, crashloop, HPA saturation) fire today; request-level SLI rules and the canary-regression alert attach when the app exporter lands. |
| [grafana-dashboard.json](./grafana-dashboard.json) | "Dula Platform Overview" dashboard (import into Grafana or provision via a ConfigMap). |

## SLO targets

| SLI | Target |
|-----|--------|
| Availability (successful requests / total) | ≥ 99.5% monthly |
| Latency (p95, read paths) | < 800 ms |
| Error budget | 0.5% / 30d (burn-rate alerting) |

## Status

- **CURRENT:** infra-signal alerts, the Helm `ServiceMonitor`, and the application Prometheus
  exporter: `platform-api` and `ai-gateway` serve `/metrics` (`dula_common.metrics`) with
  `http_requests_total` / `http_request_duration_seconds` per matched route template, and the
  AI Gateway adds `ai_call_total` / `ai_call_errors_total` / `ai_call_duration_seconds` with a
  `provider` label carrying the canary *role* (`production`/`candidate`, metered per side before
  `CanaryProvider` composes them — `dula_ai.metering`). The request-level SLI rules, the 5xx panel,
  and the `dula.mlops.canary` regression alert therefore attach to real series.
- **FUTURE:** OpenTelemetry traces (`dula_common.telemetry` is still a stub) and the worker's
  metrics (it has no HTTP listener).
- **CURRENT (M011):** production model drift detection + auto-rollback is real today, just not
  via Prometheus — `ml/dula_train/monitor.py`, run on a schedule by
  `deploy/argo/dula-ai-monitor-cronworkflow.yaml`, re-evaluates whatever is `production` against
  its own recorded baseline and appends a rollback transition on regression
  (docs/09-MLOps/ModelLifecycle.md #3-4).

Validated in CI (`deploy` job): YAML well-formedness + JSON validity.

# Observability as-code (Phase 09)

Prometheus rules and a Grafana dashboard for the Dula platform, aligned with the OTel + Prometheus
+ Grafana + Loki + Tempo stack (docs/01-Project/TechnologyStack.md, docs/16-Operations).

| File | Purpose |
|------|---------|
| [prometheus-rules.yaml](./prometheus-rules.yaml) | `PrometheusRule` — recording rules + SLO/infra alerts. Infra-signal alerts (target down, crashloop, HPA saturation) fire today; request-level SLI rules attach when the app exporter lands. |
| [grafana-dashboard.json](./grafana-dashboard.json) | "Dula Platform Overview" dashboard (import into Grafana or provision via a ConfigMap). |

## SLO targets

| SLI | Target |
|-----|--------|
| Availability (successful requests / total) | ≥ 99.5% monthly |
| Latency (p95, read paths) | < 800 ms |
| Error budget | 0.5% / 30d (burn-rate alerting) |

## Status

- **CURRENT:** infra-signal alerts + the Helm `ServiceMonitor` scaffolding.
- **FUTURE:** the application Prometheus exporter (`/metrics` with `http_request_*` histograms) —
  telemetry is currently an OTel stub (`dula_common.telemetry`); the request-level SLI rules and
  the 5xx panel attach once it emits real metrics. Tracked as a Phase 09 follow-on.

Validated in CI (`deploy` job): YAML well-formedness + JSON validity.

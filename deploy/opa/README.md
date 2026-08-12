# OPA — Authorization policy

Rego policy for Dula's RBAC + tenant-scope authorization (ADR-0009,
[../../docs/12-API/Authorization.md](../../docs/12-API/Authorization.md)).

- `policy/authz.rego` — the `dula.authz` policy; decision entrypoint `data.dula.authz.allow`.
- `policy/authz_test.rego` — policy unit tests.

## Run tests
```bash
opa test deploy/opa/policy -v
```

## Run OPA as a sidecar/service (dev)
```bash
opa run --server deploy/opa/policy
# query: POST http://localhost:8181/v1/data/dula/authz/allow  { "input": { ... } }
```

The platform-api will call OPA for authorization decisions (wired as endpoints requiring
authz are added). Phase 01 establishes the policy + contract; enforcement middleware
follows in Phase 02 alongside the first protected domain resources.

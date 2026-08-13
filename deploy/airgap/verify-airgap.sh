#!/usr/bin/env bash
# No-egress assertion for the air-gapped profile (Phase 09 acceptance; ADR-0014/0015).
# Renders the air-gapped Helm overlay and fails if it would reach outside the enclave:
#   1. no NetworkPolicy grants external egress (allowlist must be empty),
#   2. connector egress is disabled (PLUGINS_EGRESS_ENABLED=false),
#   3. every image comes from the private mirror (no public registry references),
#   4. the edge hostname is internal (no public hostname).
#
#   HELM=/path/to/helm ./verify-airgap.sh        # HELM defaults to `helm` on PATH
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CHART="${HERE}/../helm/dula"
HELM="${HELM:-helm}"
MIRROR="registry.airgap.internal/dula"

render="$("$HELM" template dula "$CHART" -f "${CHART}/values-airgapped.yaml")"
fail=0
note() { echo "AIRGAP VIOLATION: $1"; fail=1; }

# 1. No external-egress NetworkPolicy should be rendered.
if grep -q "allow-external-egress" <<<"$render"; then
  note "an external-egress NetworkPolicy is present (allowedEgressCIDRs must be empty)"
fi

# 2. Connector egress must be disabled.
if ! grep -qE 'PLUGINS_EGRESS_ENABLED:\s*"false"' <<<"$render"; then
  note "PLUGINS_EGRESS_ENABLED is not \"false\""
fi

# 3. Every image must come from the private mirror.
while read -r img; do
  case "$img" in
    "$MIRROR"/*) : ;;
    *) note "image not from the air-gap mirror: $img" ;;
  esac
done < <(grep -E '^\s*image:' <<<"$render" | sed -E 's/^\s*image:\s*//' | tr -d '"')

# 4. The edge hostname must be internal.
if grep -E 'hostname:' <<<"$render" | grep -qvE '\.internal'; then
  note "a non-internal gateway hostname is configured"
fi

if [ "$fail" -eq 0 ]; then
  echo "air-gap check passed: the air-gapped profile adds no external egress or endpoints."
fi
exit "$fail"

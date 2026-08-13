#!/usr/bin/env bash
# PostgreSQL logical backup for Dula (docs/16-Operations/DisasterRecovery.md).
# Produces a compressed custom-format dump suitable for point-in-time restore drills.
#
#   DATABASE_URL=postgres://user:pass@host:5432/dula ./pg-backup.sh <out-dir>
#
# Object storage (MinIO/S3), Qdrant snapshots, and OpenSearch snapshots are handled by their
# own operators/APIs; this script covers the primary system of record (Postgres).
set -euo pipefail

OUT_DIR="${1:-./backups}"
: "${DATABASE_URL:?set DATABASE_URL (postgres://...)}"
mkdir -p "$OUT_DIR"

ts="$(date -u +%Y%m%dT%H%M%SZ)"
out="${OUT_DIR}/dula-${ts}.dump"

echo "backing up -> ${out}"
pg_dump --format=custom --no-owner --no-privileges --file="$out" "$DATABASE_URL"

# Integrity marker for the restore drill to verify against.
sha256sum "$out" > "${out}.sha256"
echo "backup complete: ${out} ($(wc -c <"$out") bytes)"

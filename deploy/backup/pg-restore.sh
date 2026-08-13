#!/usr/bin/env bash
# PostgreSQL restore for Dula DR drills (docs/16-Operations/DisasterRecovery.md).
# Verifies the dump's checksum, then restores into the target database.
#
#   DATABASE_URL=postgres://user:pass@host:5432/dula ./pg-restore.sh <dump-file>
#
# Forward-only schema policy (ADR/PROJECT): after a restore, `alembic upgrade head` brings the
# schema to the current app version if the dump predates it.
set -euo pipefail

DUMP="${1:?usage: pg-restore.sh <dump-file>}"
: "${DATABASE_URL:?set DATABASE_URL (postgres://...)}"

if [ -f "${DUMP}.sha256" ]; then
  echo "verifying checksum"
  sha256sum -c "${DUMP}.sha256"
fi

echo "restoring ${DUMP} -> target database"
pg_restore --clean --if-exists --no-owner --no-privileges --dbname="$DATABASE_URL" "$DUMP"
echo "restore complete."

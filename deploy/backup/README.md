# Backup & Disaster Recovery scripts (Phase 09)

Backup/restore tooling for Dula's stateful tiers. Runbook + RPO/RTO targets:
[../../docs/11-Deployment/DisasterRecovery.md](../../docs/11-Deployment/DisasterRecovery.md).

| Script | Covers |
|--------|--------|
| [pg-backup.sh](./pg-backup.sh) | PostgreSQL logical backup (custom format) + SHA-256 integrity marker |
| [pg-restore.sh](./pg-restore.sh) | Checksum-verified restore for DR drills |

Postgres is the primary **system of record**. The other stateful tiers are backed up via their
native mechanisms and referenced in the DR runbook:

- **Qdrant** — collection snapshots (snapshot API / volume snapshot).
- **OpenSearch** — snapshot repository to object storage.
- **MinIO/object storage** — bucket replication / `mc mirror`.
- **Redpanda** — topic data is reprocessable; consumer offsets + schemas backed up.

## Drill

```bash
export DATABASE_URL=postgres://user:pass@host:5432/dula
deploy/backup/pg-backup.sh ./backups          # -> dula-<ts>.dump (+ .sha256)
deploy/backup/pg-restore.sh ./backups/dula-<ts>.dump   # verifies checksum, restores
alembic upgrade head                          # forward-only: bring schema to current app version
```

Scripts use standard `pg_dump`/`pg_restore` (run from a pod using the Postgres image, or any host
with the client tools). Syntax is checked in CI; the **live restore drill** against a running
Postgres with RPO/RTO measurement is an operational Phase 09 acceptance step
([../../docs/11-Deployment/DisasterRecovery.md](../../docs/11-Deployment/DisasterRecovery.md)).

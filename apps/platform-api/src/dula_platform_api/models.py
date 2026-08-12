"""ORM models (docs/07-Database/DataModel.md).

Phase 01 seeded tenants + users. Phase 02 (M002) adds the SOC/IR domain spine —
assets, alerts, incidents — plus an immutable audit trail. Every tenant-scoped table
carries `tenant_id`; RLS is enabled per table in the migrations (ADR-0006), and the
repository layer additionally scopes every query by tenant for defence-in-depth.
"""

from __future__ import annotations

import datetime as dt
import uuid
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SoftDeleteMixin:
    """Soft delete for entities where audit/history matters (DataModel.md §3)."""

    deleted_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )


class TenantEntity(Base, TimestampMixin, SoftDeleteMixin):
    """Abstract base for tenant-scoped, soft-deletable domain entities.

    Declaring ``id``/``tenant_id`` here gives the generic repository a typed surface
    (``repositories.py``) while each concrete table still gets its own columns.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )


# --- Enumerations (stored as text; validated at the schema layer) ----------------------


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Criticality(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssetType(StrEnum):
    HOST = "host"
    ACCOUNT = "account"
    CLOUD_RESOURCE = "cloud_resource"
    K8S_RESOURCE = "k8s_resource"
    OTHER = "other"


class AlertStatus(StrEnum):
    NEW = "new"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"


class IncidentStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"


# --- Identity (Phase 01) --------------------------------------------------------------


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Keycloak subject (stable OIDC `sub`).
    external_subject: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)


# --- Domain spine (Phase 02) ----------------------------------------------------------


class Asset(TenantEntity):
    """A monitored entity (host, account, cloud/K8s resource)."""

    __tablename__ = "assets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False, default=AssetType.OTHER)
    identifier: Mapped[str | None] = mapped_column(String(512), nullable=True)
    criticality: Mapped[str] = mapped_column(String(16), nullable=False, default=Criticality.MEDIUM)
    description: Mapped[str | None] = mapped_column(String(4000), nullable=True)


class Incident(TenantEntity):
    """The IR spine: a case aggregating one or more alerts."""

    __tablename__ = "incidents"

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(String(8000), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default=Severity.MEDIUM)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=IncidentStatus.OPEN)
    # OIDC subject of the assigned responder (nullable = unassigned).
    assignee_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Alert(TenantEntity):
    """A detection signal; may relate to an asset and escalate to an incident."""

    __tablename__ = "alerts"

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(String(8000), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default=Severity.MEDIUM)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=AlertStatus.NEW)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )


class AuditEvent(Base):
    """Immutable audit trail of data access / authorization decisions (DataSecurity.md).

    Append-only: no `updated_at`, no soft delete. Retention is longer than domain data
    (DataArchitecture.md §5).
    """

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

"""Request/response schemas for the domain API (docs/12-API/APIStandards.md).

Route handlers stay thin: validation lives here, business rules in ``services.py``.
Enums are validated against the same ``StrEnum`` types the ORM stores as text.
"""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, Field

from dula_platform_api.models import (
    AlertStatus,
    AssetType,
    Criticality,
    IncidentStatus,
    Severity,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Assets ---------------------------------------------------------------------------


class AssetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    asset_type: AssetType = AssetType.OTHER
    identifier: str | None = Field(default=None, max_length=512)
    criticality: Criticality = Criticality.MEDIUM
    description: str | None = Field(default=None, max_length=4000)


class AssetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    asset_type: AssetType | None = None
    identifier: str | None = Field(default=None, max_length=512)
    criticality: Criticality | None = None
    description: str | None = Field(default=None, max_length=4000)


class AssetOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    asset_type: str
    identifier: str | None
    criticality: str
    description: str | None
    created_at: dt.datetime
    updated_at: dt.datetime


# --- Incidents ------------------------------------------------------------------------


class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=8000)
    severity: Severity = Severity.MEDIUM
    status: IncidentStatus = IncidentStatus.OPEN
    assignee_subject: str | None = Field(default=None, max_length=255)


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=8000)
    severity: Severity | None = None
    status: IncidentStatus | None = None
    assignee_subject: str | None = Field(default=None, max_length=255)


class IncidentOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    title: str
    description: str | None
    severity: str
    status: str
    assignee_subject: str | None
    created_at: dt.datetime
    updated_at: dt.datetime


# --- Alerts ---------------------------------------------------------------------------


class AlertCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=8000)
    severity: Severity = Severity.MEDIUM
    status: AlertStatus = AlertStatus.NEW
    source: str | None = Field(default=None, max_length=255)
    asset_id: uuid.UUID | None = None
    incident_id: uuid.UUID | None = None


class AlertUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=8000)
    severity: Severity | None = None
    status: AlertStatus | None = None
    source: str | None = Field(default=None, max_length=255)
    asset_id: uuid.UUID | None = None
    incident_id: uuid.UUID | None = None


class AlertOut(ORMModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    title: str
    description: str | None
    severity: str
    status: str
    source: str | None
    asset_id: uuid.UUID | None
    incident_id: uuid.UUID | None
    created_at: dt.datetime
    updated_at: dt.datetime


# --- Pagination -----------------------------------------------------------------------


class Page[T](BaseModel):
    """A simple limit/offset page envelope (APIStandards.md)."""

    items: list[T]
    total: int
    limit: int
    offset: int

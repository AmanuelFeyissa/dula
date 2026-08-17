"""Tenant-scoped repositories (ports & adapters — ServiceArchitecture.md §2).

Every read and write is filtered by ``tenant_id`` and excludes soft-deleted rows. This
is the primary, deterministically-testable tenant-isolation guarantee; DB row-level
security (ADR-0006) is defence-in-depth on top of it.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any, ClassVar

from sqlalchemy import ColumnElement, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from dula_platform_api.models import Alert, Asset, Incident, TenantEntity


class UnknownSortField(ValueError):
    """Raised when a caller asks to sort by a field the repository doesn't expose.

    Kept distinct from a bare ValueError so the router can map it to 422 without
    accidentally catching an unrelated programming error the same way.
    """


def _severity_rank(column: InstrumentedAttribute[str]) -> ColumnElement[int]:
    """Order by risk, not alphabet: critical first, unrecognised values last.

    This used to live client-side (apps/web/app/*/page.tsx RANK maps), which only sorted
    the alerts on the page you happened to be looking at. Moving it here means it holds
    across pages — page 2 is never less urgent-looking than page 1 by accident.
    """
    return case(
        (column == "critical", 0),
        (column == "high", 1),
        (column == "medium", 2),
        (column == "low", 3),
        else_=4,
    )


class TenantRepository[ModelT: TenantEntity]:
    """Generic CRUD scoped to a single tenant, with filter/search/sort for ``list``.

    Subclasses declare what they support by overriding the three class attributes below;
    the base class does the tenant/soft-delete scoping and query assembly, so every
    subclass gets the same tenant-isolation guarantee for free — there is no per-model
    query to accidentally get wrong.
    """

    model: type[ModelT]
    #: Columns an unstructured `q` search matches against (OR'd, case-insensitive). Typed
    #: `Any` because both plain and nullable columns (InstrumentedAttribute[str | None])
    #: belong here, and both support `.ilike()` at runtime regardless of the stub's
    #: variance on the wrapped type.
    search_columns: ClassVar[Sequence[Any]] = ()
    #: name -> orderable expression, for the `sort` query param. Values are either columns
    #: or derived expressions (e.g. the severity-rank `case()`); both support `.asc()`/
    #: `.desc()`, which is all `_order` relies on. Typed `Any` for the same reason.
    sortable: ClassVar[dict[str, Any]] = {}
    #: Applied when no `sort` is given.
    default_order: ClassVar[Sequence[ColumnElement[Any]]] = ()

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def create(self, **values: Any) -> ModelT:
        obj = self.model(tenant_id=self._tenant_id, **values)
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def get(self, entity_id: uuid.UUID) -> ModelT | None:
        stmt = select(self.model).where(
            self.model.id == entity_id,
            self.model.tenant_id == self._tenant_id,
            self.model.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    def _order(self, sort: str | None) -> tuple[ColumnElement[Any], ...]:
        if sort is None:
            return (*self.default_order, self.model.created_at.desc())
        field = sort[1:] if sort.startswith("-") else sort
        expr = self.sortable.get(field)
        if expr is None:
            raise UnknownSortField(field)
        ordered = expr.desc() if sort.startswith("-") else expr.asc()
        return (ordered, self.model.created_at.desc())

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        equals: dict[InstrumentedAttribute[str], str] | None = None,
        sort: str | None = None,
    ) -> tuple[list[ModelT], int]:
        """List within the tenant, filtered/searched/sorted, always excluding soft-deletes.

        ``equals`` and the free-text ``q`` search are ANDed together (a filter narrows what
        the search already matched); `q` itself ORs across `search_columns`. Both apply
        identically to the page query and the count query, so `total` always matches what a
        caller could actually page through — a filtered search can never report more rows
        than it will ever return.
        """
        conditions: list[ColumnElement[bool]] = [
            self.model.tenant_id == self._tenant_id,
            self.model.deleted_at.is_(None),
        ]
        for column, value in (equals or {}).items():
            conditions.append(column == value)
        if q:
            needle = f"%{q}%"
            conditions.append(or_(*(col.ilike(needle) for col in self.search_columns)))

        order = self._order(sort)
        rows = (
            (
                await self._session.execute(
                    select(self.model)
                    .where(*conditions)
                    .order_by(*order)
                    .limit(limit)
                    .offset(offset)
                )
            )
            .scalars()
            .all()
        )
        total = (
            await self._session.execute(
                select(func.count()).select_from(self.model).where(*conditions)
            )
        ).scalar_one()
        return list(rows), total

    async def update(self, obj: ModelT, values: dict[str, Any]) -> ModelT:
        for key, value in values.items():
            setattr(obj, key, value)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def soft_delete(self, obj: ModelT) -> None:
        obj.deleted_at = func.now()
        await self._session.flush()


class AssetRepository(TenantRepository[Asset]):
    model = Asset
    search_columns = (Asset.name, Asset.identifier, Asset.description)
    sortable: ClassVar[dict[str, Any]] = {
        "name": Asset.name,
        "created_at": Asset.created_at,
        "criticality": _severity_rank(Asset.criticality),
    }
    default_order = (_severity_rank(Asset.criticality),)


class IncidentRepository(TenantRepository[Incident]):
    model = Incident
    search_columns = (Incident.title, Incident.description)
    sortable: ClassVar[dict[str, Any]] = {
        "title": Incident.title,
        "created_at": Incident.created_at,
        "severity": _severity_rank(Incident.severity),
    }
    default_order = (_severity_rank(Incident.severity),)


class AlertRepository(TenantRepository[Alert]):
    model = Alert
    search_columns = (Alert.title, Alert.description)
    sortable: ClassVar[dict[str, Any]] = {
        "title": Alert.title,
        "created_at": Alert.created_at,
        "severity": _severity_rank(Alert.severity),
    }
    default_order = (_severity_rank(Alert.severity),)

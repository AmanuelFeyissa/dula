// Domain types mirroring the Platform API schemas (docs/12-API/APIStandards.md).
// Kept hand-authored and small for Phase 02; a generated OpenAPI client can replace this
// once the API surface stabilises.

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Alert {
  id: string;
  tenant_id: string;
  title: string;
  description: string | null;
  severity: string;
  status: string;
  source: string | null;
  asset_id: string | null;
  incident_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Incident {
  id: string;
  tenant_id: string;
  title: string;
  description: string | null;
  severity: string;
  status: string;
  assignee_subject: string | null;
  created_at: string;
  updated_at: string;
}

export interface Asset {
  id: string;
  tenant_id: string;
  name: string;
  asset_type: string;
  identifier: string | null;
  criticality: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

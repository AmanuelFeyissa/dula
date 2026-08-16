import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError, apiFetch, requireAccessToken } from "@/lib/api";
import type { Incident } from "@/lib/types";

export default async function IncidentDetail({ params }: { params: Promise<{ id: string }> }) {
  const token = await requireAccessToken();
  const { id } = await params;

  let incident: Incident;
  try {
    incident = await apiFetch<Incident>(`/api/v1/incidents/${id}`, token);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    return <div className="notice notice--danger">Couldn&apos;t load this incident.</div>;
  }

  return (
    <>
      <p>
        <Link href="/incidents">← Incidents</Link>
      </p>
      <h1>{incident.title}</h1>
      <dl className="dl">
        <dt>Severity</dt>
        <dd>{incident.severity}</dd>
        <dt>Status</dt>
        <dd>{incident.status}</dd>
        <dt>Assignee</dt>
        <dd>{incident.assignee_subject ?? "—"}</dd>
        <dt>Description</dt>
        <dd>{incident.description ?? "—"}</dd>
        <dt>Created</dt>
        <dd>{incident.created_at}</dd>
      </dl>
    </>
  );
}

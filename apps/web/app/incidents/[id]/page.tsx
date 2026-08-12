import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError, apiFetch, getAccessToken } from "@/lib/api";
import { SignIn } from "@/components/SignIn";
import type { Incident } from "@/lib/types";

export default async function IncidentDetail({ params }: { params: Promise<{ id: string }> }) {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }
  const { id } = await params;

  let incident: Incident;
  try {
    incident = await apiFetch<Incident>(`/api/v1/incidents/${id}`, token);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    return <p>Failed to load incident.</p>;
  }

  return (
    <main>
      <p>
        <Link href="/incidents">← Incidents</Link>
      </p>
      <h1>{incident.title}</h1>
      <dl>
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
    </main>
  );
}

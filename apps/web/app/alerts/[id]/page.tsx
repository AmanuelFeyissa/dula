import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError, apiFetch, getAccessToken } from "@/lib/api";
import { SignIn } from "@/components/SignIn";
import type { Alert } from "@/lib/types";

export default async function AlertDetail({ params }: { params: Promise<{ id: string }> }) {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }
  const { id } = await params;

  let alert: Alert;
  try {
    alert = await apiFetch<Alert>(`/api/v1/alerts/${id}`, token);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    return <div className="notice notice--danger">Couldn&apos;t load this alert.</div>;
  }

  return (
    <>
      <p>
        <Link href="/alerts">← Alerts</Link>
      </p>
      <h1>{alert.title}</h1>
      <dl className="dl">
        <dt>Severity</dt>
        <dd>{alert.severity}</dd>
        <dt>Status</dt>
        <dd>{alert.status}</dd>
        <dt>Source</dt>
        <dd>{alert.source ?? "—"}</dd>
        <dt>Description</dt>
        <dd>{alert.description ?? "—"}</dd>
        <dt>Linked incident</dt>
        <dd>
          {alert.incident_id ? (
            <Link href={`/incidents/${alert.incident_id}`}>{alert.incident_id}</Link>
          ) : (
            "—"
          )}
        </dd>
        <dt>Linked asset</dt>
        <dd>
          {alert.asset_id ? (
            <Link href={`/assets/${alert.asset_id}`}>{alert.asset_id}</Link>
          ) : (
            "—"
          )}
        </dd>
        <dt>Created</dt>
        <dd>{alert.created_at}</dd>
      </dl>
    </>
  );
}

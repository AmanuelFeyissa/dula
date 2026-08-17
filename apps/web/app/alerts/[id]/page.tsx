import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError, apiFetch, getCurrentUser, requireAccessToken } from "@/lib/api";
import { FormError, SearchParams, humanize } from "@/components/ui";
import { can } from "@/lib/permissions";
import type { Alert } from "@/lib/types";

import { updateAlertTriage } from "../actions";
import { SEVERITIES, STATUSES } from "../constants";

export default async function AlertDetail({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<SearchParams>;
}) {
  const token = await requireAccessToken();
  const { id } = await params;
  const sp = await searchParams;
  const error = typeof sp.error === "string" ? sp.error : undefined;

  let alert: Alert;
  let canUpdate: boolean;
  try {
    const [fetchedAlert, me] = await Promise.all([
      apiFetch<Alert>(`/api/v1/alerts/${id}`, token),
      getCurrentUser(token),
    ]);
    alert = fetchedAlert;
    canUpdate = can(me.roles, "alerts.update");
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
      <FormError message={error} />
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

      {canUpdate ? (
        <div className="card" style={{ marginTop: 18 }}>
          <h2 style={{ marginTop: 0, fontSize: 15 }}>Triage</h2>
          <form action={updateAlertTriage.bind(null, id)} className="row" style={{ gap: 14 }}>
            <div className="formfield">
              <label htmlFor="status">Status</label>
              <select id="status" name="status" defaultValue={alert.status} className="select">
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {humanize(s)}
                  </option>
                ))}
              </select>
            </div>
            <div className="formfield">
              <label htmlFor="severity">Severity</label>
              <select
                id="severity"
                name="severity"
                defaultValue={alert.severity}
                className="select"
              >
                {SEVERITIES.map((s) => (
                  <option key={s} value={s}>
                    {humanize(s)}
                  </option>
                ))}
              </select>
            </div>
            <button type="submit" className="btn btn--primary" style={{ alignSelf: "flex-end" }}>
              Save
            </button>
          </form>
        </div>
      ) : null}
    </>
  );
}

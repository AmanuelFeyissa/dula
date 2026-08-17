import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError, apiFetch, getCurrentUser, requireAccessToken } from "@/lib/api";
import { FormError, SearchParams, humanize } from "@/components/ui";
import { can } from "@/lib/permissions";
import type { Incident } from "@/lib/types";

import { updateIncidentTriage } from "../actions";
import { SEVERITIES, STATUSES } from "../constants";

export default async function IncidentDetail({
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

  let incident: Incident;
  let canUpdate: boolean;
  try {
    const [fetchedIncident, me] = await Promise.all([
      apiFetch<Incident>(`/api/v1/incidents/${id}`, token),
      getCurrentUser(token),
    ]);
    incident = fetchedIncident;
    canUpdate = can(me.roles, "incidents.update");
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
      <FormError message={error} />
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

      {canUpdate ? (
        <div className="card" style={{ marginTop: 18 }}>
          <h2 style={{ marginTop: 0, fontSize: 15 }}>Triage</h2>
          <form
            action={updateIncidentTriage.bind(null, id)}
            className="row"
            style={{ gap: 14, alignItems: "flex-end" }}
          >
            <div className="formfield">
              <label htmlFor="status">Status</label>
              <select id="status" name="status" defaultValue={incident.status} className="select">
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
                defaultValue={incident.severity}
                className="select"
              >
                {SEVERITIES.map((s) => (
                  <option key={s} value={s}>
                    {humanize(s)}
                  </option>
                ))}
              </select>
            </div>
            <div className="formfield">
              <label htmlFor="assignee_subject">Assignee</label>
              <input
                id="assignee_subject"
                name="assignee_subject"
                className="input"
                defaultValue={incident.assignee_subject ?? ""}
                placeholder="Unassigned"
              />
            </div>
            <button type="submit" className="btn btn--primary">
              Save
            </button>
          </form>
        </div>
      ) : null}
    </>
  );
}

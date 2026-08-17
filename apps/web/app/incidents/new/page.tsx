import Link from "next/link";

import { FormError, PageHeader, SearchParams, humanize } from "@/components/ui";
import { getCurrentUser, requireAccessToken } from "@/lib/api";
import { can } from "@/lib/permissions";

import { createIncident } from "../actions";
import { SEVERITIES } from "../constants";

export default async function NewIncidentPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const token = await requireAccessToken();
  const sp = await searchParams;
  const error = typeof sp.error === "string" ? sp.error : undefined;
  const me = await getCurrentUser(token);

  if (!can(me.roles, "incidents.create")) {
    return (
      <>
        <PageHeader title="New incident" />
        <div className="notice notice--warn">
          <div className="notice__title">You don&apos;t have permission to create incidents</div>
          <div className="muted">
            <Link href="/incidents">← Back to incidents</Link>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <p>
        <Link href="/incidents">← Incidents</Link>
      </p>
      <PageHeader title="New incident" description="Open a case for investigation." />
      <FormError message={error} />
      <form action={createIncident} className="stack card" style={{ maxWidth: 560 }}>
        <div className="formfield">
          <label htmlFor="title">Title</label>
          <input id="title" name="title" className="input" required maxLength={512} />
        </div>
        <div className="row" style={{ gap: 14 }}>
          <div className="formfield" style={{ flex: 1 }}>
            <label htmlFor="severity">Severity</label>
            <select id="severity" name="severity" defaultValue="medium" className="select">
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>
                  {humanize(s)}
                </option>
              ))}
            </select>
          </div>
          <div className="formfield" style={{ flex: 1 }}>
            <label htmlFor="assignee_subject">Assignee</label>
            <input
              id="assignee_subject"
              name="assignee_subject"
              className="input"
              placeholder="Unassigned"
            />
          </div>
        </div>
        <div className="formfield">
          <label htmlFor="description">Description</label>
          <textarea id="description" name="description" className="textarea" maxLength={8000} />
        </div>
        <button type="submit" className="btn btn--primary" style={{ alignSelf: "flex-start" }}>
          Create incident
        </button>
      </form>
    </>
  );
}

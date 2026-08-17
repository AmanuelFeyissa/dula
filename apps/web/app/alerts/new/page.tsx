import Link from "next/link";

import { FormError, PageHeader, SearchParams, humanize } from "@/components/ui";
import { getCurrentUser, requireAccessToken } from "@/lib/api";
import { can } from "@/lib/permissions";

import { createAlert } from "../actions";
import { SEVERITIES } from "../constants";

export default async function NewAlertPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const token = await requireAccessToken();
  const sp = await searchParams;
  const error = typeof sp.error === "string" ? sp.error : undefined;
  const me = await getCurrentUser(token);

  // The link that reaches this page is already hidden for roles without alerts.create, but a
  // direct visit (or a stale bookmark after a role change) must still fail closed here — and if
  // it somehow didn't, the POST below would still be refused by OPA server-side.
  if (!can(me.roles, "alerts.create")) {
    return (
      <>
        <PageHeader title="New alert" />
        <div className="notice notice--warn">
          <div className="notice__title">You don&apos;t have permission to create alerts</div>
          <div className="muted">
            <Link href="/alerts">← Back to alerts</Link>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <p>
        <Link href="/alerts">← Alerts</Link>
      </p>
      <PageHeader title="New alert" description="Record a detection signal manually." />
      <FormError message={error} />
      <form action={createAlert} className="stack card" style={{ maxWidth: 560 }}>
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
            <label htmlFor="source">Source</label>
            <input
              id="source"
              name="source"
              className="input"
              maxLength={255}
              placeholder="e.g. edr, siem"
            />
          </div>
        </div>
        <div className="formfield">
          <label htmlFor="description">Description</label>
          <textarea id="description" name="description" className="textarea" maxLength={8000} />
        </div>
        <button type="submit" className="btn btn--primary" style={{ alignSelf: "flex-start" }}>
          Create alert
        </button>
      </form>
    </>
  );
}

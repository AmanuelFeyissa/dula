import Link from "next/link";

import { ApiError, apiFetch, requireAccessToken } from "@/lib/api";
import {
  EmptyState,
  LoadError,
  PageHeader,
  RelativeTime,
  SeverityChip,
  StatusChip,
  spineClass,
} from "@/components/ui";
import type { Incident, Page } from "@/lib/types";

const RANK: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };

export default async function IncidentsPage() {
  const token = await requireAccessToken();

  let page: Page<Incident>;
  try {
    page = await apiFetch<Page<Incident>>("/api/v1/incidents", token);
  } catch (err) {
    return (
      <>
        <PageHeader title="Incidents" description="Cases under investigation." />
        <LoadError entity="incidents" status={err instanceof ApiError ? err.status : undefined} />
      </>
    );
  }

  const incidents = [...page.items].sort(
    (a, b) => (RANK[a.severity] ?? 9) - (RANK[b.severity] ?? 9),
  );
  const active = incidents.filter((i) => !["closed", "resolved"].includes(i.status)).length;

  return (
    <>
      <PageHeader
        title="Incidents"
        description="Cases under investigation, most severe first."
        aside={
          <span className="count">
            {active} active · {page.total} total
          </span>
        }
      />

      <div className="panel">
        {incidents.length === 0 ? (
          <EmptyState
            title="No incidents"
            hint="Promote an alert, or let an agent recommend one for your approval."
          />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: "46%" }}>Incident</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Assignee</th>
                <th>Opened</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((incident) => (
                <tr key={incident.id}>
                  <td className={spineClass(incident.severity)}>
                    <Link href={`/incidents/${incident.id}`}>{incident.title}</Link>
                  </td>
                  <td>
                    <SeverityChip value={incident.severity} />
                  </td>
                  <td>
                    <StatusChip value={incident.status} />
                  </td>
                  <td className="muted">{incident.assignee_subject ?? "Unassigned"}</td>
                  <td>
                    <RelativeTime iso={incident.created_at} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

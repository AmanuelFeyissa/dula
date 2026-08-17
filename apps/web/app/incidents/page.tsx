import Link from "next/link";

import { ApiError, apiFetch, requireAccessToken } from "@/lib/api";
import {
  EmptyState,
  FilterBar,
  LoadError,
  PageHeader,
  Pagination,
  RelativeTime,
  SearchParams,
  SeverityChip,
  SortableHeader,
  StatusChip,
  spineClass,
} from "@/components/ui";
import type { Incident, Page } from "@/lib/types";

const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;
const STATUSES = ["open", "investigating", "contained", "resolved", "closed"] as const;
const DEFAULT_LIMIT = 50;

export default async function IncidentsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const token = await requireAccessToken();
  const params = await searchParams;

  const query = new URLSearchParams();
  for (const key of ["q", "severity", "status", "sort"]) {
    const value = params[key];
    if (typeof value === "string" && value !== "") query.set(key, value);
  }
  const offset = Number(params.offset) || 0;
  query.set("limit", String(DEFAULT_LIMIT));
  query.set("offset", String(offset));

  let page: Page<Incident>;
  try {
    page = await apiFetch<Page<Incident>>(`/api/v1/incidents?${query}`, token);
  } catch (err) {
    return (
      <>
        <PageHeader title="Incidents" description="Cases under investigation." />
        <LoadError entity="incidents" status={err instanceof ApiError ? err.status : undefined} />
      </>
    );
  }

  const active = page.items.filter((i) => !["closed", "resolved"].includes(i.status)).length;

  return (
    <>
      <PageHeader
        title="Incidents"
        description="Cases under investigation, most severe first."
        aside={
          <span className="count">
            {active} active on this page · {page.total} total
          </span>
        }
      />

      <div className="panel">
        <FilterBar
          basePath="/incidents"
          searchParams={params}
          filters={[
            { name: "severity", label: "Severity", options: SEVERITIES },
            { name: "status", label: "Status", options: STATUSES },
          ]}
        />
        {page.items.length === 0 ? (
          <EmptyState
            title="No incidents match"
            hint={
              params.q || params.severity || params.status
                ? "Try clearing a filter."
                : "Promote an alert, or let an agent recommend one for your approval."
            }
          />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: "46%" }}>Incident</th>
                <SortableHeader
                  basePath="/incidents"
                  searchParams={params}
                  field="severity"
                  label="Severity"
                />
                <th>Status</th>
                <th>Assignee</th>
                <SortableHeader
                  basePath="/incidents"
                  searchParams={params}
                  field="created_at"
                  label="Opened"
                />
              </tr>
            </thead>
            <tbody>
              {page.items.map((incident) => (
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
        <Pagination
          basePath="/incidents"
          searchParams={params}
          limit={DEFAULT_LIMIT}
          offset={offset}
          total={page.total}
        />
      </div>
    </>
  );
}

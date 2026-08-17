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
import type { Alert, Page } from "@/lib/types";

const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;
const STATUSES = ["new", "triaged", "in_progress", "closed", "false_positive"] as const;
const DEFAULT_LIMIT = 50;

// Server-rendered: filters, sort and page number all live in the URL, so a caller reads
// `searchParams` and forwards them to the API verbatim rather than fetching everything and
// slicing client-side — that was the old approach, and it silently broke down past one page.
export default async function AlertsPage({
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

  let page: Page<Alert>;
  try {
    page = await apiFetch<Page<Alert>>(`/api/v1/alerts?${query}`, token);
  } catch (err) {
    return (
      <>
        <PageHeader title="Alerts" description="Detection signals to triage." />
        <LoadError entity="alerts" status={err instanceof ApiError ? err.status : undefined} />
      </>
    );
  }

  const open = page.items.filter((a) => !["closed", "false_positive"].includes(a.status)).length;

  return (
    <>
      <PageHeader
        title="Alerts"
        description="Detection signals to triage, most severe first."
        aside={
          <span className="count">
            {open} open on this page · {page.total} total
          </span>
        }
      />

      <div className="panel">
        <FilterBar
          basePath="/alerts"
          searchParams={params}
          filters={[
            { name: "severity", label: "Severity", options: SEVERITIES },
            { name: "status", label: "Status", options: STATUSES },
          ]}
        />
        {page.items.length === 0 ? (
          <EmptyState
            title="No alerts match"
            hint={
              params.q || params.severity || params.status
                ? "Try clearing a filter."
                : "Detections will appear here as your connectors report them."
            }
          />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: "44%" }}>Alert</th>
                <SortableHeader
                  basePath="/alerts"
                  searchParams={params}
                  field="severity"
                  label="Severity"
                />
                <th>Status</th>
                <th>Source</th>
                <SortableHeader
                  basePath="/alerts"
                  searchParams={params}
                  field="created_at"
                  label="Seen"
                />
              </tr>
            </thead>
            <tbody>
              {page.items.map((alert) => (
                <tr key={alert.id}>
                  <td className={spineClass(alert.severity)}>
                    <Link href={`/alerts/${alert.id}`}>{alert.title}</Link>
                  </td>
                  <td>
                    <SeverityChip value={alert.severity} />
                  </td>
                  <td>
                    <StatusChip value={alert.status} />
                  </td>
                  <td className="muted">{alert.source ?? "—"}</td>
                  <td>
                    <RelativeTime iso={alert.created_at} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <Pagination
          basePath="/alerts"
          searchParams={params}
          limit={DEFAULT_LIMIT}
          offset={offset}
          total={page.total}
        />
      </div>
    </>
  );
}

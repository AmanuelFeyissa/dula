import Link from "next/link";

import { ApiError, apiFetch, getAccessToken } from "@/lib/api";
import { SignIn } from "@/components/SignIn";
import {
  EmptyState,
  LoadError,
  PageHeader,
  RelativeTime,
  SeverityChip,
  StatusChip,
  spineClass,
} from "@/components/ui";
import type { Alert, Page } from "@/lib/types";

// Severity order drives the scan: what is on fire belongs at the top, regardless of arrival time.
const RANK: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };

export default async function AlertsPage() {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }

  let page: Page<Alert>;
  try {
    page = await apiFetch<Page<Alert>>("/api/v1/alerts", token);
  } catch (err) {
    return (
      <>
        <PageHeader title="Alerts" description="Detection signals to triage." />
        <LoadError entity="alerts" status={err instanceof ApiError ? err.status : undefined} />
      </>
    );
  }

  const alerts = [...page.items].sort(
    (a, b) => (RANK[a.severity] ?? 9) - (RANK[b.severity] ?? 9),
  );
  const open = alerts.filter((a) => !["closed", "false_positive"].includes(a.status)).length;

  return (
    <>
      <PageHeader
        title="Alerts"
        description="Detection signals to triage, most severe first."
        aside={
          <span className="count">
            {open} open · {page.total} total
          </span>
        }
      />

      <div className="panel">
        {alerts.length === 0 ? (
          <EmptyState
            title="No alerts"
            hint="Detections will appear here as your connectors report them."
          />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: "44%" }}>Alert</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Source</th>
                <th>Seen</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alert) => (
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
      </div>
    </>
  );
}

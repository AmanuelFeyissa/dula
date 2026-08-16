import Link from "next/link";

import { apiFetch, requireAccessToken } from "@/lib/api";
import { PageHeader, RelativeTime, SeverityChip, spineClass } from "@/components/ui";
import type { Alert, Asset, Incident, Page } from "@/lib/types";

const RANK: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };

async function safePage<T>(path: string, token: string): Promise<Page<T> | null> {
  try {
    return await apiFetch<Page<T>>(path, token);
  } catch {
    return null;
  }
}

function Metric({ label, value, href }: { label: string; value: string; href: string }) {
  return (
    <Link href={href} className="card" style={{ textDecoration: "none", color: "inherit" }}>
      <div
        className="faint"
        style={{ fontSize: 11, letterSpacing: "0.07em", textTransform: "uppercase" }}
      >
        {label}
      </div>
      <div
        style={{ fontSize: 26, fontWeight: 650, marginTop: 4, fontVariantNumeric: "tabular-nums" }}
      >
        {value}
      </div>
    </Link>
  );
}

export default async function Home() {
  const token = await requireAccessToken();

  const [alerts, incidents, assets] = await Promise.all([
    safePage<Alert>("/api/v1/alerts", token),
    safePage<Incident>("/api/v1/incidents", token),
    safePage<Asset>("/api/v1/assets", token),
  ]);

  const openAlerts = (alerts?.items ?? []).filter(
    (a) => !["closed", "false_positive"].includes(a.status),
  );
  const critical = openAlerts.filter((a) => a.severity === "critical");
  const activeIncidents = (incidents?.items ?? []).filter(
    (i) => !["closed", "resolved"].includes(i.status),
  );
  const needsAttention = [...openAlerts]
    .sort((a, b) => (RANK[a.severity] ?? 9) - (RANK[b.severity] ?? 9))
    .slice(0, 5);

  return (
    <>
      <PageHeader
        title="Situation overview"
        description="What needs a human right now, and where to start."
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
          gap: 12,
          marginBottom: 24,
        }}
      >
        <Metric label="Critical open" value={String(critical.length)} href="/alerts" />
        <Metric label="Open alerts" value={String(openAlerts.length)} href="/alerts" />
        <Metric label="Active incidents" value={String(activeIncidents.length)} href="/incidents" />
        <Metric label="Assets monitored" value={String(assets?.total ?? 0)} href="/assets" />
      </div>

      <h2>Needs attention</h2>
      <div className="panel" style={{ marginBottom: 24 }}>
        {needsAttention.length === 0 ? (
          <div className="empty">
            <div className="empty__title">Nothing open</div>
            <div style={{ fontSize: 14 }}>Every alert is closed or triaged.</div>
          </div>
        ) : (
          <table className="table">
            <tbody>
              {needsAttention.map((alert) => (
                <tr key={alert.id}>
                  <td className={spineClass(alert.severity)} style={{ width: "52%" }}>
                    <Link href={`/alerts/${alert.id}`}>{alert.title}</Link>
                  </td>
                  <td>
                    <SeverityChip value={alert.severity} />
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

      <h2>Work it with Dula</h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
          gap: 12,
        }}
      >
        <Link href="/agents" className="card" style={{ textDecoration: "none", color: "inherit" }}>
          <strong>Investigate with an agent</strong>
          <p className="muted" style={{ margin: "6px 0 0", fontSize: 13.5 }}>
            Triage, enrich, and corroborate automatically. Consequential actions wait for your
            approval.
          </p>
        </Link>
        <Link
          href="/automation"
          className="card"
          style={{ textDecoration: "none", color: "inherit" }}
        >
          <strong>Run a playbook</strong>
          <p className="muted" style={{ margin: "6px 0 0", fontSize: 13.5 }}>
            A saved procedure end to end, with an approval checkpoint and a grounded report.
          </p>
        </Link>
        <Link href="/intel" className="card" style={{ textDecoration: "none", color: "inherit" }}>
          <strong>Analyse intelligence</strong>
          <p className="muted" style={{ margin: "6px 0 0", fontSize: 13.5 }}>
            Extract IOCs and ATT&amp;CK techniques, prioritise a CVE, or author a detection rule.
          </p>
        </Link>
      </div>
    </>
  );
}

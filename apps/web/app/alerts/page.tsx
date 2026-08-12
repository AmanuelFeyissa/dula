import Link from "next/link";

import { apiFetch, getAccessToken } from "@/lib/api";
import { SignIn } from "@/components/SignIn";
import type { Alert, Page } from "@/lib/types";

const cell = { padding: "0.4rem 0.6rem", borderBottom: "1px solid #eee", textAlign: "left" } as const;

export default async function AlertsPage() {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }

  let page: Page<Alert>;
  try {
    page = await apiFetch<Page<Alert>>("/api/v1/alerts", token);
  } catch {
    return <p>Failed to load alerts. Ensure the Platform API is reachable.</p>;
  }

  return (
    <main>
      <h1>Alerts</h1>
      <p>{page.total} total</p>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th style={cell}>Title</th>
            <th style={cell}>Severity</th>
            <th style={cell}>Status</th>
            <th style={cell}>Source</th>
          </tr>
        </thead>
        <tbody>
          {page.items.map((alert) => (
            <tr key={alert.id}>
              <td style={cell}>
                <Link href={`/alerts/${alert.id}`}>{alert.title}</Link>
              </td>
              <td style={cell}>{alert.severity}</td>
              <td style={cell}>{alert.status}</td>
              <td style={cell}>{alert.source ?? "—"}</td>
            </tr>
          ))}
          {page.items.length === 0 ? (
            <tr>
              <td style={cell} colSpan={4}>
                No alerts yet.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </main>
  );
}

import Link from "next/link";

import { apiFetch, getAccessToken } from "@/lib/api";
import { SignIn } from "@/components/SignIn";
import type { Incident, Page } from "@/lib/types";

const cell = { padding: "0.4rem 0.6rem", borderBottom: "1px solid #eee", textAlign: "left" } as const;

export default async function IncidentsPage() {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }

  let page: Page<Incident>;
  try {
    page = await apiFetch<Page<Incident>>("/api/v1/incidents", token);
  } catch {
    return <p>Failed to load incidents. Ensure the Platform API is reachable.</p>;
  }

  return (
    <main>
      <h1>Incidents</h1>
      <p>{page.total} total</p>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th style={cell}>Title</th>
            <th style={cell}>Severity</th>
            <th style={cell}>Status</th>
            <th style={cell}>Assignee</th>
          </tr>
        </thead>
        <tbody>
          {page.items.map((incident) => (
            <tr key={incident.id}>
              <td style={cell}>
                <Link href={`/incidents/${incident.id}`}>{incident.title}</Link>
              </td>
              <td style={cell}>{incident.severity}</td>
              <td style={cell}>{incident.status}</td>
              <td style={cell}>{incident.assignee_subject ?? "—"}</td>
            </tr>
          ))}
          {page.items.length === 0 ? (
            <tr>
              <td style={cell} colSpan={4}>
                No incidents yet.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </main>
  );
}

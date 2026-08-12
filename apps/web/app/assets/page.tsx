import Link from "next/link";

import { apiFetch, getAccessToken } from "@/lib/api";
import { SignIn } from "@/components/SignIn";
import type { Asset, Page } from "@/lib/types";

const cell = { padding: "0.4rem 0.6rem", borderBottom: "1px solid #eee", textAlign: "left" } as const;

export default async function AssetsPage() {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }

  let page: Page<Asset>;
  try {
    page = await apiFetch<Page<Asset>>("/api/v1/assets", token);
  } catch {
    return <p>Failed to load assets. Ensure the Platform API is reachable.</p>;
  }

  return (
    <main>
      <h1>Assets</h1>
      <p>{page.total} total</p>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th style={cell}>Name</th>
            <th style={cell}>Type</th>
            <th style={cell}>Criticality</th>
            <th style={cell}>Identifier</th>
          </tr>
        </thead>
        <tbody>
          {page.items.map((asset) => (
            <tr key={asset.id}>
              <td style={cell}>
                <Link href={`/assets/${asset.id}`}>{asset.name}</Link>
              </td>
              <td style={cell}>{asset.asset_type}</td>
              <td style={cell}>{asset.criticality}</td>
              <td style={cell}>{asset.identifier ?? "—"}</td>
            </tr>
          ))}
          {page.items.length === 0 ? (
            <tr>
              <td style={cell} colSpan={4}>
                No assets yet.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </main>
  );
}

import Link from "next/link";

import { ApiError, apiFetch, getAccessToken } from "@/lib/api";
import { SignIn } from "@/components/SignIn";
import {
  EmptyState,
  LoadError,
  PageHeader,
  SeverityChip,
  humanize,
  spineClass,
} from "@/components/ui";
import type { Asset, Page } from "@/lib/types";

const RANK: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };

export default async function AssetsPage() {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }

  let page: Page<Asset>;
  try {
    page = await apiFetch<Page<Asset>>("/api/v1/assets", token);
  } catch (err) {
    return (
      <>
        <PageHeader title="Assets" description="Monitored hosts, accounts, and resources." />
        <LoadError entity="assets" status={err instanceof ApiError ? err.status : undefined} />
      </>
    );
  }

  // Criticality drives blast radius, so the most critical assets lead.
  const assets = [...page.items].sort(
    (a, b) => (RANK[a.criticality] ?? 9) - (RANK[b.criticality] ?? 9),
  );

  return (
    <>
      <PageHeader
        title="Assets"
        description="Monitored hosts, accounts, and resources, most critical first."
        aside={<span className="count">{page.total} total</span>}
      />

      <div className="panel">
        {assets.length === 0 ? (
          <EmptyState title="No assets" hint="Assets appear as your inventory sources sync." />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: "28%" }}>Asset</th>
                <th>Type</th>
                <th>Criticality</th>
                <th>Identifier</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => (
                <tr key={asset.id}>
                  <td className={spineClass(asset.criticality)}>
                    <Link href={`/assets/${asset.id}`}>{asset.name}</Link>
                  </td>
                  <td className="muted">{humanize(asset.asset_type)}</td>
                  <td>
                    <SeverityChip value={asset.criticality} />
                  </td>
                  <td className="mono muted">{asset.identifier ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

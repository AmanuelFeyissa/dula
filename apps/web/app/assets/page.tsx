import Link from "next/link";

import { ApiError, apiFetch, requireAccessToken } from "@/lib/api";
import {
  EmptyState,
  FilterBar,
  LoadError,
  PageHeader,
  Pagination,
  SearchParams,
  SeverityChip,
  SortableHeader,
  humanize,
  spineClass,
} from "@/components/ui";
import type { Asset, Page } from "@/lib/types";

const CRITICALITIES = ["critical", "high", "medium", "low"] as const;
const DEFAULT_LIMIT = 50;

export default async function AssetsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const token = await requireAccessToken();
  const params = await searchParams;

  const query = new URLSearchParams();
  for (const key of ["q", "criticality", "sort"]) {
    const value = params[key];
    if (typeof value === "string" && value !== "") query.set(key, value);
  }
  const offset = Number(params.offset) || 0;
  query.set("limit", String(DEFAULT_LIMIT));
  query.set("offset", String(offset));

  let page: Page<Asset>;
  try {
    page = await apiFetch<Page<Asset>>(`/api/v1/assets?${query}`, token);
  } catch (err) {
    return (
      <>
        <PageHeader title="Assets" description="Monitored hosts, accounts, and resources." />
        <LoadError entity="assets" status={err instanceof ApiError ? err.status : undefined} />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Assets"
        description="Monitored hosts, accounts, and resources, most critical first."
        aside={<span className="count">{page.total} total</span>}
      />

      <div className="panel">
        <FilterBar
          basePath="/assets"
          searchParams={params}
          filters={[{ name: "criticality", label: "Criticality", options: CRITICALITIES }]}
        />
        {page.items.length === 0 ? (
          <EmptyState
            title="No assets match"
            hint={
              params.q || params.criticality
                ? "Try clearing a filter."
                : "Assets appear as your inventory sources sync."
            }
          />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: "28%" }}>Asset</th>
                <th>Type</th>
                <SortableHeader
                  basePath="/assets"
                  searchParams={params}
                  field="criticality"
                  label="Criticality"
                />
                <th>Identifier</th>
              </tr>
            </thead>
            <tbody>
              {page.items.map((asset) => (
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
        <Pagination
          basePath="/assets"
          searchParams={params}
          limit={DEFAULT_LIMIT}
          offset={offset}
          total={page.total}
        />
      </div>
    </>
  );
}

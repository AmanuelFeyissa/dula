import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError, apiFetch, getCurrentUser, requireAccessToken } from "@/lib/api";
import { FormError, SearchParams, humanize } from "@/components/ui";
import { can } from "@/lib/permissions";
import type { Asset } from "@/lib/types";

import { updateAssetTriage } from "../actions";
import { CRITICALITIES } from "../constants";

export default async function AssetDetail({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<SearchParams>;
}) {
  const token = await requireAccessToken();
  const { id } = await params;
  const sp = await searchParams;
  const error = typeof sp.error === "string" ? sp.error : undefined;

  let asset: Asset;
  let canUpdate: boolean;
  try {
    const [fetchedAsset, me] = await Promise.all([
      apiFetch<Asset>(`/api/v1/assets/${id}`, token),
      getCurrentUser(token),
    ]);
    asset = fetchedAsset;
    canUpdate = can(me.roles, "assets.update");
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    return <div className="notice notice--danger">Couldn&apos;t load this asset.</div>;
  }

  return (
    <>
      <p>
        <Link href="/assets">← Assets</Link>
      </p>
      <h1>{asset.name}</h1>
      <FormError message={error} />
      <dl className="dl">
        <dt>Type</dt>
        <dd>{humanize(asset.asset_type)}</dd>
        <dt>Criticality</dt>
        <dd>{asset.criticality}</dd>
        <dt>Identifier</dt>
        <dd>{asset.identifier ?? "—"}</dd>
        <dt>Description</dt>
        <dd>{asset.description ?? "—"}</dd>
        <dt>Created</dt>
        <dd>{asset.created_at}</dd>
      </dl>

      {canUpdate ? (
        <div className="card" style={{ marginTop: 18 }}>
          <h2 style={{ marginTop: 0, fontSize: 15 }}>Triage</h2>
          <form
            action={updateAssetTriage.bind(null, id)}
            className="row"
            style={{ gap: 14, alignItems: "flex-end" }}
          >
            <div className="formfield">
              <label htmlFor="criticality">Criticality</label>
              <select
                id="criticality"
                name="criticality"
                defaultValue={asset.criticality}
                className="select"
              >
                {CRITICALITIES.map((c) => (
                  <option key={c} value={c}>
                    {humanize(c)}
                  </option>
                ))}
              </select>
            </div>
            <button type="submit" className="btn btn--primary">
              Save
            </button>
          </form>
        </div>
      ) : null}
    </>
  );
}

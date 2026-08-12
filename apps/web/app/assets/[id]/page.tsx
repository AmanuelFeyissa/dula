import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError, apiFetch, getAccessToken } from "@/lib/api";
import { SignIn } from "@/components/SignIn";
import type { Asset } from "@/lib/types";

export default async function AssetDetail({ params }: { params: Promise<{ id: string }> }) {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }
  const { id } = await params;

  let asset: Asset;
  try {
    asset = await apiFetch<Asset>(`/api/v1/assets/${id}`, token);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    return <p>Failed to load asset.</p>;
  }

  return (
    <main>
      <p>
        <Link href="/assets">← Assets</Link>
      </p>
      <h1>{asset.name}</h1>
      <dl>
        <dt>Type</dt>
        <dd>{asset.asset_type}</dd>
        <dt>Criticality</dt>
        <dd>{asset.criticality}</dd>
        <dt>Identifier</dt>
        <dd>{asset.identifier ?? "—"}</dd>
        <dt>Description</dt>
        <dd>{asset.description ?? "—"}</dd>
        <dt>Created</dt>
        <dd>{asset.created_at}</dd>
      </dl>
    </main>
  );
}

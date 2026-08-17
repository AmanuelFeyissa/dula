import Link from "next/link";

import { FormError, PageHeader, SearchParams, humanize } from "@/components/ui";
import { getCurrentUser, requireAccessToken } from "@/lib/api";
import { can } from "@/lib/permissions";

import { createAsset } from "../actions";
import { CRITICALITIES } from "../constants";

export default async function NewAssetPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const token = await requireAccessToken();
  const sp = await searchParams;
  const error = typeof sp.error === "string" ? sp.error : undefined;
  const me = await getCurrentUser(token);

  if (!can(me.roles, "assets.create")) {
    return (
      <>
        <PageHeader title="New asset" />
        <div className="notice notice--warn">
          <div className="notice__title">You don&apos;t have permission to create assets</div>
          <div className="muted">
            <Link href="/assets">← Back to assets</Link>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <p>
        <Link href="/assets">← Assets</Link>
      </p>
      <PageHeader title="New asset" description="Add a host, account, or resource to inventory." />
      <FormError message={error} />
      <form action={createAsset} className="stack card" style={{ maxWidth: 560 }}>
        <div className="formfield">
          <label htmlFor="name">Name</label>
          <input id="name" name="name" className="input" required maxLength={255} />
        </div>
        <div className="row" style={{ gap: 14 }}>
          <div className="formfield" style={{ flex: 1 }}>
            <label htmlFor="criticality">Criticality</label>
            <select id="criticality" name="criticality" defaultValue="medium" className="select">
              {CRITICALITIES.map((c) => (
                <option key={c} value={c}>
                  {humanize(c)}
                </option>
              ))}
            </select>
          </div>
          <div className="formfield" style={{ flex: 1 }}>
            <label htmlFor="identifier">Identifier</label>
            <input
              id="identifier"
              name="identifier"
              className="input mono"
              maxLength={512}
              placeholder="hostname, IP, or account ID"
            />
          </div>
        </div>
        <div className="formfield">
          <label htmlFor="description">Description</label>
          <textarea id="description" name="description" className="textarea" maxLength={4000} />
        </div>
        <button type="submit" className="btn btn--primary" style={{ alignSelf: "flex-start" }}>
          Create asset
        </button>
      </form>
    </>
  );
}

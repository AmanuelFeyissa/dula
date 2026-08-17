"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { ApiError, apiFetch, requireAccessToken } from "@/lib/api";
import type { Asset } from "@/lib/types";

function str(formData: FormData, key: string): string | undefined {
  const value = formData.get(key);
  return typeof value === "string" && value !== "" ? value : undefined;
}

function messageFor(err: unknown, permissionMessage: string): string {
  if (err instanceof ApiError && (err.status === 403 || err.status === 401)) {
    return permissionMessage;
  }
  return "Something went wrong. Try again.";
}

export async function updateAssetTriage(id: string, formData: FormData): Promise<void> {
  const token = await requireAccessToken();
  const body: Record<string, string> = {};
  const criticality = str(formData, "criticality");
  if (criticality) body.criticality = criticality;

  try {
    await apiFetch<Asset>(`/api/v1/assets/${id}`, token, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  } catch (err) {
    const message = messageFor(err, "You don't have permission to update this asset.");
    redirect(`/assets/${id}?error=${encodeURIComponent(message)}`);
  }

  revalidatePath(`/assets/${id}`);
  revalidatePath("/assets");
  redirect(`/assets/${id}`);
}

export async function createAsset(formData: FormData): Promise<void> {
  const token = await requireAccessToken();
  const name = str(formData, "name");
  if (!name) {
    redirect(`/assets/new?error=${encodeURIComponent("Name is required.")}`);
  }

  const body: Record<string, unknown> = { name };
  const criticality = str(formData, "criticality");
  const identifier = str(formData, "identifier");
  const description = str(formData, "description");
  if (criticality) body.criticality = criticality;
  if (identifier) body.identifier = identifier;
  if (description) body.description = description;

  let created: Asset;
  try {
    created = await apiFetch<Asset>("/api/v1/assets", token, {
      method: "POST",
      body: JSON.stringify(body),
    });
  } catch (err) {
    const message = messageFor(err, "You don't have permission to create assets.");
    redirect(`/assets/new?error=${encodeURIComponent(message)}`);
  }

  revalidatePath("/assets");
  redirect(`/assets/${created.id}`);
}

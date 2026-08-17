"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { ApiError, apiFetch, requireAccessToken } from "@/lib/api";
import type { Alert } from "@/lib/types";

// Triage edits and creation only — delete stays API-only (M010 plan, decision D). Both actions
// bounce failures back to the originating page as a `?error=` param rather than holding client
// state, so the form works identically with JavaScript on or off.

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

export async function updateAlertTriage(id: string, formData: FormData): Promise<void> {
  const token = await requireAccessToken();
  const body: Record<string, string> = {};
  const status = str(formData, "status");
  const severity = str(formData, "severity");
  if (status) body.status = status;
  if (severity) body.severity = severity;

  try {
    await apiFetch<Alert>(`/api/v1/alerts/${id}`, token, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  } catch (err) {
    const message = messageFor(err, "You don't have permission to update this alert.");
    redirect(`/alerts/${id}?error=${encodeURIComponent(message)}`);
  }

  revalidatePath(`/alerts/${id}`);
  revalidatePath("/alerts");
  redirect(`/alerts/${id}`);
}

export async function createAlert(formData: FormData): Promise<void> {
  const token = await requireAccessToken();
  const title = str(formData, "title");
  if (!title) {
    redirect(`/alerts/new?error=${encodeURIComponent("Title is required.")}`);
  }

  const body: Record<string, unknown> = { title };
  const severity = str(formData, "severity");
  const description = str(formData, "description");
  const source = str(formData, "source");
  if (severity) body.severity = severity;
  if (description) body.description = description;
  if (source) body.source = source;

  let created: Alert;
  try {
    created = await apiFetch<Alert>("/api/v1/alerts", token, {
      method: "POST",
      body: JSON.stringify(body),
    });
  } catch (err) {
    const message = messageFor(err, "You don't have permission to create alerts.");
    redirect(`/alerts/new?error=${encodeURIComponent(message)}`);
  }

  revalidatePath("/alerts");
  redirect(`/alerts/${created.id}`);
}

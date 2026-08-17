"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { ApiError, apiFetch, requireAccessToken } from "@/lib/api";
import type { Incident } from "@/lib/types";

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

export async function updateIncidentTriage(id: string, formData: FormData): Promise<void> {
  const token = await requireAccessToken();
  const body: Record<string, string> = {};
  const status = str(formData, "status");
  const severity = str(formData, "severity");
  const assignee = str(formData, "assignee_subject");
  if (status) body.status = status;
  if (severity) body.severity = severity;
  if (assignee) body.assignee_subject = assignee;

  try {
    await apiFetch<Incident>(`/api/v1/incidents/${id}`, token, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  } catch (err) {
    const message = messageFor(err, "You don't have permission to update this incident.");
    redirect(`/incidents/${id}?error=${encodeURIComponent(message)}`);
  }

  revalidatePath(`/incidents/${id}`);
  revalidatePath("/incidents");
  redirect(`/incidents/${id}`);
}

export async function createIncident(formData: FormData): Promise<void> {
  const token = await requireAccessToken();
  const title = str(formData, "title");
  if (!title) {
    redirect(`/incidents/new?error=${encodeURIComponent("Title is required.")}`);
  }

  const body: Record<string, unknown> = { title };
  const severity = str(formData, "severity");
  const description = str(formData, "description");
  const assignee = str(formData, "assignee_subject");
  if (severity) body.severity = severity;
  if (description) body.description = description;
  if (assignee) body.assignee_subject = assignee;

  let created: Incident;
  try {
    created = await apiFetch<Incident>("/api/v1/incidents", token, {
      method: "POST",
      body: JSON.stringify(body),
    });
  } catch (err) {
    const message = messageFor(err, "You don't have permission to create incidents.");
    redirect(`/incidents/new?error=${encodeURIComponent(message)}`);
  }

  revalidatePath("/incidents");
  redirect(`/incidents/${created.id}`);
}

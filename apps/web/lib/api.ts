import { redirect } from "next/navigation";

import { auth } from "@/auth";

// Server-side typed client for the Platform API. The caller's Keycloak access token is
// forwarded so the API enforces authN/authZ and tenant scoping (ADR-0006/0009).
const API_URL = process.env.PLATFORM_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * The token for a server component, or a redirect into the sign-in flow.
 *
 * Pages use this rather than null-checking a session themselves: middleware.ts already blocks
 * unauthenticated requests, so reaching here without a token means the session went stale
 * mid-render, and the only useful response is to re-authenticate. Keycloak re-issues silently
 * when the SSO session is still alive, so the operator usually sees nothing at all.
 *
 * Route handlers under app/api/ deliberately do NOT use this — they must answer with a 401,
 * not a redirect, so they read `auth()` directly.
 */
export async function requireAccessToken(): Promise<string> {
  const session = await auth();
  if (!session?.accessToken || session.error) {
    redirect("/signin");
  }
  return session.accessToken;
}

export async function apiFetch<T>(
  path: string,
  token: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new ApiError(res.status, `API ${res.status}`);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

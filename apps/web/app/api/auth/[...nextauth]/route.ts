import type { NextRequest } from "next/server";

import { handlers } from "@/auth";

export const POST = handlers.POST;

// Auth.js serves the session object at GET /api/auth/session, and that endpoint returns
// whatever the `session` callback produced — including the Keycloak access token and id token
// that server code needs. The session cookie is HttpOnly, but the endpoint is not: any script
// running on this origin can fetch it. That would turn an XSS into an exfiltrated bearer token
// usable directly against the Platform API and AI Gateway from anywhere, rather than one
// confined to same-origin requests through this server.
//
// So the tokens are stripped on the way out. Server code is unaffected: `auth()` reads the
// session in-process and never goes through this endpoint. Nothing on the client consumes
// them — the browser talks to the proxy routes under app/api/, which authenticate by cookie.
const TOKEN_FIELDS = ["accessToken", "idToken"] as const;

export async function GET(request: NextRequest): Promise<Response> {
  const response = await handlers.GET(request);

  if (!request.nextUrl.pathname.endsWith("/session")) {
    return response;
  }

  const body: unknown = await response
    .clone()
    .json()
    .catch(() => null);
  if (body === null || typeof body !== "object") {
    return response;
  }

  const safe = { ...(body as Record<string, unknown>) };
  for (const field of TOKEN_FIELDS) {
    delete safe[field];
  }

  // Carry the original headers so Set-Cookie (session rotation) survives, but drop the stale
  // content-length — the body is shorter now.
  const headers = new Headers(response.headers);
  headers.delete("content-length");

  return new Response(JSON.stringify(safe), { status: response.status, headers });
}

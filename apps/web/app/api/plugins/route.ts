import { auth } from "@/auth";

// Server-side proxy: list installed plugins/connectors. Injects the caller's Keycloak token.
const AI_GATEWAY_URL = process.env.AI_GATEWAY_URL ?? "http://localhost:8100";

export async function GET(): Promise<Response> {
  const session = await auth();
  const token = session?.accessToken;
  if (!token) {
    return new Response("Unauthorized", { status: 401 });
  }
  const upstream = await fetch(`${AI_GATEWAY_URL}/api/v1/plugins`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await upstream.text();
  return new Response(body, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}

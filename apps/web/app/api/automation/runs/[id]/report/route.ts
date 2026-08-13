import { auth } from "@/auth";

// Server-side proxy: read a run's grounded report. Injects the caller's Keycloak token.
const AI_GATEWAY_URL = process.env.AI_GATEWAY_URL ?? "http://localhost:8100";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const session = await auth();
  const token = session?.accessToken;
  if (!token) {
    return new Response("Unauthorized", { status: 401 });
  }
  const { id } = await params;

  const upstream = await fetch(`${AI_GATEWAY_URL}/api/v1/automation/runs/${id}/report`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await upstream.text();
  return new Response(body, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}

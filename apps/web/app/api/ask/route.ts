import { auth } from "@/auth";

// Server-side proxy: injects the caller's Keycloak token and streams the AI Gateway's SSE
// response back to the browser. The access token never reaches the client.
const AI_GATEWAY_URL = process.env.AI_GATEWAY_URL ?? "http://localhost:8100";

export async function POST(req: Request): Promise<Response> {
  const session = await auth();
  const token = session?.accessToken;
  if (!token) {
    return new Response("Unauthorized", { status: 401 });
  }
  const { question } = (await req.json()) as { question?: string };
  if (!question) {
    return new Response("Missing question", { status: 400 });
  }

  const upstream = await fetch(`${AI_GATEWAY_URL}/api/v1/ask/stream`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(`AI Gateway error ${upstream.status}`, { status: upstream.status });
  }
  return new Response(upstream.body, {
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-store" },
  });
}

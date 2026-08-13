import { auth } from "@/auth";

// Server-side proxy: start a playbook run. Injects the caller's Keycloak token.
const AI_GATEWAY_URL = process.env.AI_GATEWAY_URL ?? "http://localhost:8100";

export async function POST(
  req: Request,
  { params }: { params: Promise<{ name: string }> },
): Promise<Response> {
  const session = await auth();
  const token = session?.accessToken;
  if (!token) {
    return new Response("Unauthorized", { status: 401 });
  }
  const { name } = await params;
  const payload = await req.json();

  const upstream = await fetch(
    `${AI_GATEWAY_URL}/api/v1/automation/playbooks/${name}/runs`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  const body = await upstream.text();
  return new Response(body, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}

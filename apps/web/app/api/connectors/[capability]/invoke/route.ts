import { auth } from "@/auth";

// Server-side proxy: invoke a read connector capability. Injects the caller's token.
const AI_GATEWAY_URL = process.env.AI_GATEWAY_URL ?? "http://localhost:8100";

export async function POST(
  req: Request,
  { params }: { params: Promise<{ capability: string }> },
): Promise<Response> {
  const session = await auth();
  const token = session?.accessToken;
  if (!token) {
    return new Response("Unauthorized", { status: 401 });
  }
  const { capability } = await params;
  const payload = await req.json();

  const upstream = await fetch(
    `${AI_GATEWAY_URL}/api/v1/connectors/${encodeURIComponent(capability)}/invoke`,
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

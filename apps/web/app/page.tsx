import { auth, signIn, signOut } from "@/auth";

const API_URL = process.env.PLATFORM_API_URL ?? "http://localhost:8000";

async function fetchMe(accessToken: string): Promise<{ ok: boolean; body: unknown }> {
  try {
    const res = await fetch(`${API_URL}/api/v1/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    return { ok: res.ok, body: res.ok ? await res.json() : `API ${res.status}` };
  } catch {
    return { ok: false, body: "Platform API unreachable" };
  }
}

export default async function Home() {
  const session = await auth();
  const me = session?.accessToken ? await fetchMe(session.accessToken) : null;

  return (
    <main>
      <h1>Dula</h1>
      <p>Cybersecurity AI Platform — Phase 01 foundation.</p>

      {session?.user ? (
        <>
          <p>
            Signed in as <strong>{session.user.name ?? session.user.email}</strong>.
          </p>
          <form
            action={async () => {
              "use server";
              await signOut({ redirectTo: "/" });
            }}
          >
            <button type="submit">Sign out</button>
          </form>

          <h2>GET /api/v1/me</h2>
          <pre
            style={{
              background: "#111",
              color: "#0f0",
              padding: "1rem",
              borderRadius: 8,
              overflowX: "auto",
            }}
          >
            {JSON.stringify(me?.body ?? null, null, 2)}
          </pre>
        </>
      ) : (
        <form
          action={async () => {
            "use server";
            await signIn("keycloak", { redirectTo: "/" });
          }}
        >
          <button type="submit">Sign in with Keycloak</button>
        </form>
      )}
    </main>
  );
}

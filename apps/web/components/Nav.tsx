import Link from "next/link";

import { auth, signOut } from "@/auth";

const linkStyle = { marginRight: "1rem" } as const;

// Top navigation for the authenticated app shell.
export async function Nav() {
  const session = await auth();
  return (
    <nav
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        borderBottom: "1px solid #ddd",
        paddingBottom: "0.75rem",
        marginBottom: "1.5rem",
      }}
    >
      <Link href="/" style={{ ...linkStyle, fontWeight: 700 }}>
        Dula
      </Link>
      <Link href="/alerts" style={linkStyle}>
        Alerts
      </Link>
      <Link href="/incidents" style={linkStyle}>
        Incidents
      </Link>
      <Link href="/assets" style={linkStyle}>
        Assets
      </Link>
      <Link href="/ask" style={linkStyle}>
        Ask
      </Link>
      <Link href="/intel" style={linkStyle}>
        Intel
      </Link>
      <Link href="/agents" style={linkStyle}>
        Agents
      </Link>
      <Link href="/integrations" style={linkStyle}>
        Integrations
      </Link>
      <Link href="/automation" style={linkStyle}>
        Automation
      </Link>
      <span style={{ flex: 1 }} />
      {session?.user ? (
        <form
          action={async () => {
            "use server";
            await signOut({ redirectTo: "/" });
          }}
        >
          <button type="submit">Sign out ({session.user.name ?? session.user.email})</button>
        </form>
      ) : null}
    </nav>
  );
}

import Link from "next/link";
import { redirect } from "next/navigation";

import { auth, signOut } from "@/auth";
import { NavLink } from "@/components/NavLink";

// Grouping mirrors how the product is actually built: the operational spine, the intelligence
// layer on top of it, and the autonomy layer that acts through both.
const GROUPS: { label: string; items: { href: string; label: string }[] }[] = [
  {
    label: "Operations",
    items: [
      { href: "/alerts", label: "Alerts" },
      { href: "/incidents", label: "Incidents" },
      { href: "/assets", label: "Assets" },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { href: "/ask", label: "Ask Dula" },
      { href: "/intel", label: "Cyber Intel" },
    ],
  },
  {
    label: "Autonomy",
    items: [
      { href: "/agents", label: "Agents" },
      { href: "/automation", label: "Playbooks" },
      { href: "/integrations", label: "Integrations" },
    ],
  },
];

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}

export async function Nav() {
  const session = await auth();
  const name = session?.user?.name ?? session?.user?.email ?? "Signed in";

  return (
    <nav className="sidebar" aria-label="Main">
      <Link className="brand" href="/">
        <span className="brand__mark" aria-hidden="true">
          D
        </span>
        <span>
          <span className="brand__name">Dula</span>
          <span className="brand__sub">Security AI</span>
        </span>
      </Link>

      {GROUPS.map((group) => (
        <div className="navgroup" key={group.label}>
          <div className="navgroup__label">{group.label}</div>
          {group.items.map((item) => (
            <NavLink key={item.href} href={item.href}>
              {item.label}
            </NavLink>
          ))}
        </div>
      ))}

      {session?.user ? (
        <div className="sidebar__foot">
          <div className="who">
            <span className="who__avatar" aria-hidden="true">
              {initials(name)}
            </span>
            <span className="who__name">{name}</span>
          </div>
          <form
            action={async () => {
              "use server";
              // Clearing only Dula's own cookie leaves the Keycloak SSO session alive, so the
              // next sign-in silently re-authenticates the same person — which is why switching
              // accounts previously meant recreating the Keycloak container. RP-initiated
              // logout (OpenID Connect RP-Initiated Logout 1.0) ends both sessions.
              const current = await auth();
              const idToken = current?.idToken;
              await signOut({ redirect: false });

              const issuer =
                process.env.KEYCLOAK_ISSUER ?? "http://localhost:8080/realms/dula";
              const logout = new URL(`${issuer}/protocol/openid-connect/logout`);
              logout.searchParams.set(
                "client_id",
                process.env.KEYCLOAK_CLIENT_ID ?? "dula-web",
              );
              logout.searchParams.set(
                "post_logout_redirect_uri",
                process.env.AUTH_URL ?? "http://localhost:3000",
              );
              // Without the hint Keycloak interrupts with its own "are you sure?" page.
              if (idToken) {
                logout.searchParams.set("id_token_hint", idToken);
              }
              redirect(logout.toString());
            }}
          >
            <button type="submit" className="btn btn--ghost" style={{ width: "100%" }}>
              Sign out
            </button>
          </form>
        </div>
      ) : null}
    </nav>
  );
}

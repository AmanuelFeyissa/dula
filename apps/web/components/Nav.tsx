import Link from "next/link";

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
              await signOut({ redirectTo: "/" });
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

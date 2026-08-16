"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

// Knowing where you are is the cheapest orientation a nav can give. `aria-current` drives both
// the visual active state (globals.css) and the screen-reader announcement.
export function NavLink({ href, children }: { href: string; children: ReactNode }) {
  const pathname = usePathname();
  const active = pathname === href || pathname.startsWith(`${href}/`);
  return (
    <Link href={href} className="navlink" aria-current={active ? "page" : undefined}>
      {children}
    </Link>
  );
}

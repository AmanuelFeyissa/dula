import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";
import { Nav } from "@/components/Nav";
import { auth } from "@/auth";

export const metadata: Metadata = {
  title: "Dula — Security AI Platform",
  description: "Dula — Cybersecurity AI Platform",
};

export default async function RootLayout({ children }: { children: ReactNode }) {
  const session = await auth();

  // Signed out, the app chrome is just noise — the sign-in screen owns the whole viewport.
  if (!session?.user) {
    return (
      <html lang="en">
        <body>{children}</body>
      </html>
    );
  }

  return (
    <html lang="en">
      <body>
        <div className="shell">
          <Nav />
          <div className="content">{children}</div>
        </div>
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Nav } from "@/components/Nav";

export const metadata: Metadata = {
  title: "Dula",
  description: "Dula — Cybersecurity AI Platform",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        style={{
          fontFamily: "system-ui, sans-serif",
          margin: 0,
          padding: "2rem",
          maxWidth: 960,
        }}
      >
        <Nav />
        {children}
      </body>
    </html>
  );
}

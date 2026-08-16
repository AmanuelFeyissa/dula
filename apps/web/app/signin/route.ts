import type { NextRequest } from "next/server";

import { signIn } from "@/auth";

// Starting the OIDC flow needs to write the PKCE verifier cookie, which Next.js only permits
// from a route handler or a server action — never from a server component. That is why /signin
// is a route rather than a page: there is no interstitial to render, and no provider to choose
// (Keycloak is the only one), so the operator goes straight to the Dula-themed login page.
export async function GET(request: NextRequest) {
  const requested = request.nextUrl.searchParams.get("callbackUrl") ?? "/";

  // Only same-origin paths. `//evil.example` is a protocol-relative URL that a browser treats
  // as absolute, so a leading-slash check alone would be an open redirect.
  const redirectTo = requested.startsWith("/") && !requested.startsWith("//") ? requested : "/";

  // Throws NEXT_REDIRECT, which Next.js turns into the 302 to Keycloak.
  return signIn("keycloak", { redirectTo });
}

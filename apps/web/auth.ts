import NextAuth from "next-auth";
import Keycloak from "next-auth/providers/keycloak";

// Keycloak OIDC via Auth.js (ADR-0009). `dula-web` is a public client (PKCE, no secret),
// so we use token_endpoint_auth_method: "none". The realm-issued access token is carried
// on the session so the server can call the Platform API on the user's behalf.
//
// The secret must be OMITTED ENTIRELY for a public client: passing `clientSecret: ""` still
// sets the property, and the OAuth layer then fails the token exchange with
// `"client.client_secret" property must not be provided when none client authentication
// method is used`. Supplying a non-empty secret switches to a confidential client.
const clientSecret = process.env.KEYCLOAK_CLIENT_SECRET?.trim();

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Keycloak({
      clientId: process.env.KEYCLOAK_CLIENT_ID ?? "dula-web",
      issuer: process.env.KEYCLOAK_ISSUER ?? "http://localhost:8080/realms/dula",
      ...(clientSecret
        ? { clientSecret }
        : { client: { token_endpoint_auth_method: "none" } }),
    }),
  ],
  // Keycloak is the only identity provider, so an in-app provider chooser would be a dead
  // click. `/signin` is a route handler that starts the OIDC flow immediately; the operator
  // lands straight on the Dula-themed Keycloak page
  // (deploy/docker/keycloak/themes/dula/). Failures divert to /auth/error so they stay
  // readable instead of redirect-looping.
  pages: { signIn: "/signin", error: "/auth/error" },
  callbacks: {
    // Consulted by middleware.ts for every matched route.
    authorized({ auth: session }) {
      // A failed refresh means the tokens are dead even though the cookie looks fine. Treating
      // it as unauthorized sends the user back through Keycloak, which re-issues silently if
      // the SSO session is still alive — so in practice this is invisible.
      if (session?.error === "RefreshTokenError") {
        return false;
      }
      return !!session?.user;
    },
    // Keycloak access tokens are short-lived (realm accessTokenLifespan = 300s in dev). Without
    // refresh, every API call starts failing with 401 a few minutes after sign-in while the UI
    // still looks signed in. So: keep the refresh token, and renew shortly before expiry.
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.expiresAt = account.expires_at;
        // Kept for RP-initiated logout: Keycloak needs `id_token_hint` to end the SSO session
        // without showing the user a confirmation page (see Nav.tsx).
        token.idToken = account.id_token;
        return token;
      }

      const expiresAt = token.expiresAt ?? 0;
      // 30s of slack so a request in flight never races the expiry.
      if (Date.now() < expiresAt * 1000 - 30_000) {
        return token;
      }
      if (!token.refreshToken) {
        return { ...token, error: "RefreshTokenError" as const };
      }

      try {
        const issuer = process.env.KEYCLOAK_ISSUER ?? "http://localhost:8080/realms/dula";
        const res = await fetch(`${issuer}/protocol/openid-connect/token`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({
            grant_type: "refresh_token",
            client_id: process.env.KEYCLOAK_CLIENT_ID ?? "dula-web",
            refresh_token: token.refreshToken,
            ...(clientSecret ? { client_secret: clientSecret } : {}),
          }),
        });
        const refreshed = (await res.json()) as {
          access_token?: string;
          refresh_token?: string;
          expires_in?: number;
        };
        if (!res.ok || !refreshed.access_token) {
          throw new Error(`refresh failed (${res.status})`);
        }
        return {
          ...token,
          accessToken: refreshed.access_token,
          refreshToken: refreshed.refresh_token ?? token.refreshToken,
          expiresAt: Math.floor(Date.now() / 1000) + (refreshed.expires_in ?? 300),
          error: undefined,
        };
      } catch {
        // Surface the failure so the UI can ask the user to sign in again rather than
        // showing a misleading "backend unreachable" error.
        return { ...token, error: "RefreshTokenError" as const };
      }
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      session.idToken = token.idToken;
      session.error = token.error;
      // The refresh token is deliberately NOT copied onto the session: it is long-lived, and
      // the session object is readable by the browser via /api/auth/session.
      return session;
    },
  },
});

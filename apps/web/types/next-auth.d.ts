import "next-auth";
import "next-auth/jwt";

// Carry the Keycloak access token through the session/JWT (see auth.ts).
// Keycloak access tokens are short-lived (realm `accessTokenLifespan`, 300s in dev), so the
// refresh token and expiry ride along too and the token is refreshed before it expires.
declare module "next-auth" {
  interface Session {
    accessToken?: string;
    // Needed as `id_token_hint` for RP-initiated logout. Note the refresh token is absent by
    // design: the session is readable by the browser via /api/auth/session.
    idToken?: string;
    error?: "RefreshTokenError";
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    idToken?: string;
    expiresAt?: number;
    error?: "RefreshTokenError";
  }
}

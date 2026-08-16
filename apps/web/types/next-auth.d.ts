import "next-auth";
import "next-auth/jwt";

// Carry the Keycloak access token through the session/JWT (see auth.ts).
// Keycloak access tokens are short-lived (realm `accessTokenLifespan`, 300s in dev), so the
// refresh token and expiry ride along too and the token is refreshed before it expires.
declare module "next-auth" {
  interface Session {
    accessToken?: string;
    error?: "RefreshTokenError";
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    expiresAt?: number;
    error?: "RefreshTokenError";
  }
}

import "next-auth";
import "next-auth/jwt";

// Carry the Keycloak access token through the session/JWT (see auth.ts).
declare module "next-auth" {
  interface Session {
    accessToken?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
  }
}

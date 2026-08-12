import NextAuth from "next-auth";
import Keycloak from "next-auth/providers/keycloak";

// Keycloak OIDC via Auth.js (ADR-0009). `dula-web` is a public client (PKCE, no secret),
// so we use token_endpoint_auth_method: "none". The realm-issued access token is carried
// on the session so the server can call the Platform API on the user's behalf.
export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Keycloak({
      clientId: process.env.KEYCLOAK_CLIENT_ID ?? "dula-web",
      issuer: process.env.KEYCLOAK_ISSUER ?? "http://localhost:8080/realms/dula",
      clientSecret: process.env.KEYCLOAK_CLIENT_SECRET ?? "",
      client: { token_endpoint_auth_method: "none" },
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account?.access_token) {
        token.accessToken = account.access_token;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      return session;
    },
  },
});

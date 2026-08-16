export { auth as middleware } from "@/auth";

// Authentication is enforced here rather than page-by-page, so a new page is protected by
// default instead of by remembering to add a guard. The decision itself lives in the
// `authorized` callback in auth.ts; unauthenticated requests are sent to /signin, which starts
// the OIDC flow immediately.
//
// Server components still call requireAccessToken() (lib/api.ts) — that is defence in depth,
// not duplication: it also covers the case where the cookie is valid but the token has gone
// stale between the middleware check and the render.
export const config = {
  matcher: [
    /*
     * Everything except:
     *   api/auth   — the Auth.js endpoints themselves (callback, session, csrf)
     *   signin     — the route that starts the flow; guarding it would loop
     *   auth/error — must stay reachable while signed out, or failures are invisible
     *   _next/*    — build output
     *   static assets by extension
     */
    "/((?!api/auth|signin|auth/error|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};

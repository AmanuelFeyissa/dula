import Link from "next/link";

// The only page an unauthenticated operator can actually see. It exists so a broken sign-in
// says what broke instead of bouncing between /signin and Keycloak forever.
//
// Auth.js appends ?error=<code>. The copy below is deliberately about what the reader should
// do next; the code itself is kept visible because the person debugging this is usually an
// administrator reading over someone's shoulder.
const EXPLANATIONS: Record<string, { title: string; detail: string }> = {
  Configuration: {
    title: "Dula is not configured correctly",
    detail:
      "The connection between Dula and Keycloak is misconfigured, so sign-in cannot start. " +
      "This is a server-side problem — an administrator needs to check the Keycloak issuer, " +
      "client ID and redirect URIs. Signing in again will not help until it is fixed.",
  },
  AccessDenied: {
    title: "Access denied",
    detail:
      "Keycloak authenticated you but declined to release an account for Dula. Your account " +
      "may be disabled, or it may not be assigned to a tenant yet. Contact an administrator.",
  },
  Verification: {
    title: "That sign-in link has expired",
    detail: "Sign-in links are single-use and short-lived. Start again.",
  },
};

const FALLBACK = {
  title: "Sign-in did not complete",
  detail:
    "Something interrupted the sign-in exchange with Keycloak. This is usually transient — " +
    "try again, and contact an administrator if it keeps happening.",
};

export default async function AuthErrorPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const raw = params.error;
  const code = typeof raw === "string" ? raw : undefined;
  const { title, detail } = (code && EXPLANATIONS[code]) || FALLBACK;

  return (
    <main className="signin">
      <section className="signin__card">
        <div
          className="brand__mark"
          aria-hidden="true"
          style={{ width: 40, height: 40, fontSize: 20, margin: "0 auto 16px" }}
        >
          D
        </div>
        <h1 style={{ fontSize: 21, margin: 0 }}>{title}</h1>
        <p className="page__desc" style={{ margin: "10px auto 22px", textAlign: "left" }}>
          {detail}
        </p>
        <Link href="/signin" className="btn btn--primary" style={{ width: "100%" }}>
          Try signing in again
        </Link>
        {code ? (
          <p className="mono" style={{ marginTop: 16, fontSize: 12, color: "var(--text-faint)" }}>
            Error code: {code}
          </p>
        ) : null}
      </section>
    </main>
  );
}

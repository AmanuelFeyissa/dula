import { signIn } from "@/auth";

// Sign-in prompt shown on protected pages when there is no session (Keycloak OIDC).
export function SignIn() {
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
        <h1 style={{ fontSize: 22 }}>Sign in to Dula</h1>
        <p className="page__desc" style={{ margin: "8px auto 22px" }}>
          Your security operations, intelligence, and supervised automation — in one place.
        </p>
        <form
          action={async () => {
            "use server";
            await signIn("keycloak", { redirectTo: "/" });
          }}
        >
          <button type="submit" className="btn btn--primary" style={{ width: "100%" }}>
            Continue with Keycloak
          </button>
        </form>
      </section>
    </main>
  );
}

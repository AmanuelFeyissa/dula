import { signIn } from "@/auth";

// Sign-in prompt shown on protected pages when there is no session (Keycloak OIDC).
export function SignIn() {
  return (
    <section>
      <h1>Sign in required</h1>
      <p>Access to Dula requires authentication.</p>
      <form
        action={async () => {
          "use server";
          await signIn("keycloak", { redirectTo: "/" });
        }}
      >
        <button type="submit">Sign in with Keycloak</button>
      </form>
    </section>
  );
}

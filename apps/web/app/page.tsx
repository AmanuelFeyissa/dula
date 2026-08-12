import Link from "next/link";

import { getAccessToken } from "@/lib/api";
import { SignIn } from "@/components/SignIn";

export default async function Home() {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }
  return (
    <main>
      <h1>Dula</h1>
      <p>Cybersecurity AI Platform — Phase 02 core platform.</p>
      <p>Manage your security operations spine:</p>
      <ul>
        <li>
          <Link href="/alerts">Alerts</Link> — detection signals to triage.
        </li>
        <li>
          <Link href="/incidents">Incidents</Link> — cases under investigation.
        </li>
        <li>
          <Link href="/assets">Assets</Link> — monitored hosts, accounts, and resources.
        </li>
      </ul>
    </main>
  );
}

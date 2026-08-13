import { getAccessToken } from "@/lib/api";
import { AgentConsole } from "@/components/AgentConsole";
import { SignIn } from "@/components/SignIn";

export default async function AgentsPage() {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }
  return <AgentConsole />;
}

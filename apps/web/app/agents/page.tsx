import { requireAccessToken } from "@/lib/api";
import { AgentConsole } from "@/components/AgentConsole";

export default async function AgentsPage() {
  const token = await requireAccessToken();
  return <AgentConsole />;
}

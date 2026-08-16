import { requireAccessToken } from "@/lib/api";
import { IntegrationsConsole } from "@/components/IntegrationsConsole";

export default async function IntegrationsPage() {
  const token = await requireAccessToken();
  return <IntegrationsConsole />;
}

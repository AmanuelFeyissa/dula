import { requireAccessToken } from "@/lib/api";
import { AutomationConsole } from "@/components/AutomationConsole";

export default async function AutomationPage() {
  const token = await requireAccessToken();
  return <AutomationConsole />;
}

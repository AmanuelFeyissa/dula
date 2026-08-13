import { getAccessToken } from "@/lib/api";
import { IntegrationsConsole } from "@/components/IntegrationsConsole";
import { SignIn } from "@/components/SignIn";

export default async function IntegrationsPage() {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }
  return <IntegrationsConsole />;
}

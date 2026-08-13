import { getAccessToken } from "@/lib/api";
import { AutomationConsole } from "@/components/AutomationConsole";
import { SignIn } from "@/components/SignIn";

export default async function AutomationPage() {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }
  return <AutomationConsole />;
}

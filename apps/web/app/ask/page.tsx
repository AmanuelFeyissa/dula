import { getAccessToken } from "@/lib/api";
import { AskConsole } from "@/components/AskConsole";
import { SignIn } from "@/components/SignIn";

export default async function AskPage() {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }
  return <AskConsole />;
}

import { requireAccessToken } from "@/lib/api";
import { AskConsole } from "@/components/AskConsole";

export default async function AskPage() {
  const token = await requireAccessToken();
  return <AskConsole />;
}

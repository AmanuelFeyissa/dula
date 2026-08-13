import { getAccessToken } from "@/lib/api";
import { IntelWorkbench } from "@/components/IntelWorkbench";
import { SignIn } from "@/components/SignIn";

export default async function IntelPage() {
  const token = await getAccessToken();
  if (!token) {
    return <SignIn />;
  }
  return <IntelWorkbench />;
}

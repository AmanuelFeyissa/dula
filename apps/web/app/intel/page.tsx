import { requireAccessToken } from "@/lib/api";
import { IntelWorkbench } from "@/components/IntelWorkbench";

export default async function IntelPage() {
  const token = await requireAccessToken();
  return <IntelWorkbench />;
}

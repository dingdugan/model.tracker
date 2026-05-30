import { getModels } from "@/lib/queries";
import { ModelsTable } from "./models/ModelsTable";

export const revalidate = 300;

export default async function HomePage() {
  const models = await getModels().catch(() => []);
  return <ModelsTable models={models} />;
}

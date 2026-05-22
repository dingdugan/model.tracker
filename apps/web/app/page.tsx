import { getModels } from "@/lib/queries";
import { ModelsTable } from "./models/ModelsTable";

export const revalidate = 1800;

export default async function HomePage() {
  const models = await getModels().catch(() => []);
  return <ModelsTable models={models} />;
}

import { ModelsTable } from "./ModelsTable";
import { getModels } from "@/lib/queries";

export const revalidate = 1800;

export default async function ModelsPage() {
  const models = await getModels().catch(() => []);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">All models</h1>
        <p className="text-ink-muted">Filter, sort, and compare every model we track.</p>
      </div>
      <ModelsTable models={models} />
    </div>
  );
}

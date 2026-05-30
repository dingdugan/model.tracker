import { getModels } from "@/lib/queries";
import { CompareClient } from "./CompareClient";

export const revalidate = 300;

export default async function ComparePage() {
  const models = await getModels().catch(() => []);

  // Default: model with highest Arena ELO (most interesting starting point)
  const defaultModel = [...models].sort((a, b) => (b.arena_elo ?? -1) - (a.arena_elo ?? -1))[0];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Compare models</h1>
        <p className="text-ink-muted text-sm mt-1">Select up to 5 models to compare side by side.</p>
      </div>
      <CompareClient models={models} defaultModelId={defaultModel?.id ?? null} />
    </div>
  );
}

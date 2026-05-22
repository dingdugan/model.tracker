import { supabase } from "./supabase";
import type {
  BenchmarkScore,
  DailySnapshot,
  ModelOverview,
  PriceHistoryPoint,
  Vendor,
} from "./types";

// Revalidate every 30 min — scraper triggers a redeploy anyway.
export const revalidate = 1800;

export async function getModels(): Promise<ModelOverview[]> {
  const { data, error } = await supabase
    .from("models_overview")
    .select("*")
    .neq("status", "retired")
    .order("arena_elo", { ascending: false, nullsFirst: false });
  if (error) throw error;
  return (data ?? []) as ModelOverview[];
}

export async function getModelById(id: string): Promise<ModelOverview | null> {
  const { data, error } = await supabase
    .from("models_overview")
    .select("*")
    .eq("id", id)
    .maybeSingle();
  if (error) throw error;
  return (data as ModelOverview) ?? null;
}

export async function getVendors(): Promise<Vendor[]> {
  const { data, error } = await supabase.from("vendors").select("*").order("name");
  if (error) throw error;
  return (data ?? []) as Vendor[];
}

export async function getPriceHistory(modelId: string): Promise<PriceHistoryPoint[]> {
  const { data, error } = await supabase
    .from("prices")
    .select("effective_date,input_per_mtok,output_per_mtok,cached_input_per_mtok,currency")
    .eq("model_id", modelId)
    .order("effective_date", { ascending: true });
  if (error) throw error;
  return (data ?? []) as PriceHistoryPoint[];
}

export async function getCurrentBenchmarks(modelId: string): Promise<BenchmarkScore[]> {
  const { data, error } = await supabase
    .from("current_benchmarks")
    .select("*")
    .eq("model_id", modelId);
  if (error) throw error;
  return (data ?? []) as BenchmarkScore[];
}

export async function getLeaderboard(benchmark: string, limit = 30): Promise<Array<BenchmarkScore & { name: string; vendor_name: string }>> {
  const { data, error } = await supabase
    .from("current_benchmarks")
    .select("model_id, score, score_unit, score_max, source, measured_at")
    .eq("benchmark_name", benchmark)
    .order("score", { ascending: false })
    .limit(limit);
  if (error) throw error;
  const scores = (data ?? []) as BenchmarkScore[];
  if (scores.length === 0) return [];

  const ids = scores.map((s) => s.model_id);
  const { data: models, error: e2 } = await supabase
    .from("models_overview")
    .select("id, name, vendor_name")
    .in("id", ids);
  if (e2) throw e2;
  const lookup = new Map((models ?? []).map((m: any) => [m.id, m]));
  return scores
    .map((s) => {
      const m = lookup.get(s.model_id);
      return m ? { ...s, name: m.name, vendor_name: m.vendor_name } : null;
    })
    .filter((x): x is BenchmarkScore & { name: string; vendor_name: string } => x !== null);
}

export async function getRecentSnapshots(days = 30): Promise<DailySnapshot[]> {
  const { data, error } = await supabase
    .from("daily_snapshots")
    .select("*")
    .order("snapshot_date", { ascending: false })
    .limit(days);
  if (error) throw error;
  return (data ?? []) as DailySnapshot[];
}

export async function getLatestSnapshot(): Promise<DailySnapshot | null> {
  const { data, error } = await supabase
    .from("daily_snapshots")
    .select("*")
    .order("snapshot_date", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error) throw error;
  return (data as DailySnapshot) ?? null;
}

export async function getBenchmarkNames(): Promise<string[]> {
  const { data, error } = await supabase
    .from("benchmark_scores")
    .select("benchmark_name");
  if (error) throw error;
  const set = new Set<string>();
  (data ?? []).forEach((r: any) => set.add(r.benchmark_name));
  return Array.from(set).sort();
}

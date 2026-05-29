import { supabase } from "./supabase";
import type {
  BenchmarkScore,
  ChangelogDay,
  DailySnapshot,
  DiscoveryCandidateRow,
  ModelOverview,
  PendingChangeRow,
  PriceHistoryPoint,
  ScrapeIssueRow,
  StalePrice,
  Vendor,
} from "./types";

export const revalidate = 1800;

// ── Data health (Phase D) ──────────────────────────────────────────────────

export async function getDiscoveryCandidates(): Promise<DiscoveryCandidateRow[]> {
  const { data, error } = await supabase
    .from("discovery_candidates")
    .select("source, reported_name, vendor_guess, occurrences, first_seen, last_seen")
    .eq("status", "new")
    .order("last_seen", { ascending: false });
  if (error) throw error;
  return (data ?? []) as DiscoveryCandidateRow[];
}

export async function getPendingChanges(): Promise<PendingChangeRow[]> {
  const { data, error } = await supabase
    .from("pending_changes")
    .select("kind, model_id, field, prior_value, proposed_value, reason, occurrences, last_seen")
    .eq("status", "pending")
    .order("last_seen", { ascending: false });
  if (error) throw error;
  return (data ?? []) as PendingChangeRow[];
}

export async function getRecentIssues(limit = 30): Promise<ScrapeIssueRow[]> {
  const { data, error } = await supabase
    .from("recent_scrape_issues")
    .select("stage, vendor_id, benchmark, error_class, occurred_at")
    .limit(limit);
  if (error) throw error;
  return (data ?? []) as ScrapeIssueRow[];
}

export async function getStalePrices(days = 30): Promise<StalePrice[]> {
  const cutoff = new Date(Date.now() - days * 86_400_000).toISOString().slice(0, 10);
  const { data, error } = await supabase
    .from("models_overview")
    .select("id, name, vendor_name, price_effective_date, status, input_per_mtok")
    .neq("status", "retired")
    .not("input_per_mtok", "is", null)
    .lt("price_effective_date", cutoff)
    .order("price_effective_date", { ascending: true });
  if (error) throw error;
  return (data ?? []) as StalePrice[];
}

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

export async function getChangelog(days = 60): Promise<ChangelogDay[]> {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  const cutoffStr = cutoff.toISOString().slice(0, 10);

  const [eventsRes, snapshotsRes] = await Promise.all([
    supabase
      .from("price_change_events")
      .select("model_id, changed_at, input_old, input_new, output_old, output_new, cached_input_old, cached_input_new, currency")
      .gte("changed_at", cutoffStr)
      .order("changed_at", { ascending: false }),
    supabase
      .from("daily_snapshots")
      .select("snapshot_date, new_models")
      .gte("snapshot_date", cutoffStr)
      .order("snapshot_date", { ascending: false }),
  ]);

  const events = eventsRes.data ?? [];
  const snapshots = snapshotsRes.data ?? [];

  // Fetch model names for price events
  const modelIds = [...new Set(events.map((e: any) => e.model_id))];
  const nameMap = new Map<string, string>();
  if (modelIds.length > 0) {
    const { data: names } = await supabase
      .from("models")
      .select("id, name")
      .in("id", modelIds);
    (names ?? []).forEach((m: any) => nameMap.set(m.id, m.name));
  }

  // Build per-date map
  const byDate = new Map<string, ChangelogDay>();

  for (const snap of snapshots) {
    byDate.set(snap.snapshot_date, {
      date: snap.snapshot_date,
      newModels: (snap.new_models ?? []).map((m: any) => ({
        id: m.id,
        name: m.name,
        vendor: m.vendor,
      })),
      priceChanges: [],
    });
  }

  for (const ev of events) {
    const d = ev.changed_at;
    if (!byDate.has(d)) {
      byDate.set(d, { date: d, newModels: [], priceChanges: [] });
    }
    byDate.get(d)!.priceChanges.push({
      model_id: ev.model_id,
      model_name: nameMap.get(ev.model_id) ?? ev.model_id.split("/")[1],
      changed_at: ev.changed_at,
      input_old: ev.input_old,
      input_new: ev.input_new,
      output_old: ev.output_old,
      output_new: ev.output_new,
      cached_input_old: ev.cached_input_old,
      cached_input_new: ev.cached_input_new,
      currency: ev.currency ?? "USD",
    });
  }

  return Array.from(byDate.values()).sort((a, b) => b.date.localeCompare(a.date));
}

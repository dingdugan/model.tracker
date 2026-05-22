export type ModelOverview = {
  id: string;
  vendor_id: string;
  vendor_name: string;
  vendor_country: string;
  slug: string;
  name: string;
  family: string | null;
  release_date: string | null;
  context_window: number | null;
  max_output_tokens: number | null;
  modalities: string[];
  is_open_weight: boolean;
  parameters_b: number | null;
  license: string | null;
  status: "active" | "preview" | "deprecated" | "retired";
  announcement_url: string | null;
  description: string | null;
  input_per_mtok: number | null;
  output_per_mtok: number | null;
  cached_input_per_mtok: number | null;
  currency: string | null;
  price_effective_date: string | null;
  arena_elo: number | null;
  first_seen: string;
  last_seen: string;
};

export type Vendor = {
  id: string;
  name: string;
  country: string;
  website: string | null;
  pricing_url: string | null;
  models_url: string | null;
  blog_url: string | null;
};

export type PriceHistoryPoint = {
  effective_date: string;
  input_per_mtok: number | null;
  output_per_mtok: number | null;
  cached_input_per_mtok: number | null;
  currency: string;
};

export type BenchmarkScore = {
  model_id: string;
  benchmark_name: string;
  score: number;
  score_unit: string;
  score_max: number | null;
  source: string;
  source_url: string | null;
  measured_at: string | null;
};

export type DailySnapshot = {
  snapshot_date: string;
  vendors_count: number;
  models_count: number;
  active_count: number;
  new_models: Array<{ id: string; name: string; vendor: string; release_date: string | null }>;
  price_changes: Array<{ model_id: string; field: string; old: number | null; new: number | null }>;
  status_changes: Array<{ id: string; old_status: string; new_status: string }>;
  bench_changes: Array<{ model_id: string; benchmark: string; old: number; new: number }>;
};

export type PriceChangeEvent = {
  model_id: string;
  model_name: string;
  changed_at: string;
  input_old: number | null;
  input_new: number | null;
  output_old: number | null;
  output_new: number | null;
  cached_input_old: number | null;
  cached_input_new: number | null;
  currency: string;
};

export type ChangelogDay = {
  date: string;
  newModels: Array<{ id: string; name: string; vendor: string }>;
  priceChanges: PriceChangeEvent[];
};

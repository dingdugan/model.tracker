import Link from "next/link";
import { notFound } from "next/navigation";
import { Card, CardHeader } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { getCurrentBenchmarks, getModelById, getPriceHistory } from "@/lib/queries";
import { countryFlag, fmtDate, fmtElo, fmtPct, fmtPrice, fmtTokens } from "@/lib/format";
import { PriceChart } from "./PriceChart";
import { BenchmarkRadar } from "./BenchmarkRadar";

export const revalidate = 1800;

export default async function ModelPage({ params }: { params: Promise<{ id: string[] }> }) {
  const { id: segments } = await params;
  const id = segments.map(decodeURIComponent).join("/");

  const [model, priceHistory, benchmarks] = await Promise.all([
    getModelById(id).catch(() => null),
    getPriceHistory(id).catch(() => []),
    getCurrentBenchmarks(id).catch(() => []),
  ]);
  if (!model) notFound();

  const arena = benchmarks.find((b) => b.benchmark_name === "arena-elo");
  const academic = benchmarks.filter((b) => ["mmlu", "gpqa", "humaneval", "swe-bench-verified", "math"].includes(b.benchmark_name));

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-end gap-4">
        <div className="flex-1">
          <Link href="/models" className="text-xs text-ink-muted hover:text-accent">← All models</Link>
          <h1 className="text-3xl font-semibold tracking-tight mt-1 flex items-center gap-3">
            {model.name}
            {model.is_open_weight && <Badge tone="ok">open-weight</Badge>}
            {model.status !== "active" && <Badge tone={model.status === "preview" ? "warn" : "muted"}>{model.status}</Badge>}
          </h1>
          <p className="text-ink-muted mt-1">
            <span className="mr-1.5">{countryFlag(model.vendor_country)}</span>
            {model.vendor_name} · {model.family ?? "—"}
            {model.release_date && ` · released ${model.release_date}`}
          </p>
          {model.description && <p className="mt-3 max-w-2xl text-sm">{model.description}</p>}
        </div>
        <div className="grid grid-cols-3 gap-6 text-sm">
          <Stat label="Context"      value={fmtTokens(model.context_window)} />
          <Stat label="Max output"   value={fmtTokens(model.max_output_tokens)} />
          <Stat label="Parameters"   value={model.parameters_b != null ? `${model.parameters_b}B` : "—"} />
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <Card className="md:col-span-1">
          <CardHeader title="Current price" subtitle={model.price_effective_date ? fmtDate(model.price_effective_date) : undefined} />
          <div className="p-5 space-y-3 text-sm">
            <Row k="Input"   v={`${fmtPrice(model.input_per_mtok)}/Mtok`} />
            <Row k="Output"  v={`${fmtPrice(model.output_per_mtok)}/Mtok`} />
            <Row k="Cached"  v={`${fmtPrice(model.cached_input_per_mtok)}/Mtok`} />
            <Row k="Currency" v={model.currency ?? "USD"} />
            {model.announcement_url && (
              <a href={model.announcement_url} target="_blank" rel="noreferrer"
                className="block text-xs text-ink-muted hover:text-accent pt-2 border-t border-paper-line">
                Announcement →
              </a>
            )}
          </div>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader title="Price history" subtitle="USD per 1M tokens" />
          <div className="p-5">
            {priceHistory.length === 0 ? (
              <p className="text-sm text-ink-muted py-12 text-center">No price history yet.</p>
            ) : (
              <PriceChart data={priceHistory} />
            )}
          </div>
        </Card>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Benchmarks" subtitle="Latest scores" />
          <div className="p-5">
            {benchmarks.length === 0 ? (
              <p className="text-sm text-ink-muted py-8 text-center">No benchmark data yet.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {arena && (
                  <li className="flex justify-between border-b border-paper-line pb-2">
                    <span className="font-medium">Arena Elo (LMSYS)</span>
                    <span className="font-mono">{fmtElo(arena.score)}</span>
                  </li>
                )}
                {benchmarks
                  .filter((b) => b.benchmark_name !== "arena-elo")
                  .map((b) => (
                    <li key={b.benchmark_name} className="flex justify-between">
                      <span>{b.benchmark_name}</span>
                      <span className="font-mono">
                        {b.score_unit === "pct" ? fmtPct(b.score) :
                         b.score_unit === "elo" ? fmtElo(b.score) :
                         b.score.toFixed(1)}
                      </span>
                    </li>
                  ))}
              </ul>
            )}
          </div>
        </Card>

        <Card>
          <CardHeader title="Skill profile" subtitle="Academic benchmarks" />
          <div className="p-5">
            {academic.length === 0 ? (
              <p className="text-sm text-ink-muted py-8 text-center">No academic benchmarks yet.</p>
            ) : (
              <BenchmarkRadar scores={academic.map(b => ({ name: b.benchmark_name, value: b.score }))} />
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wider text-ink-muted">{label}</div>
      <div className="font-mono text-lg">{value}</div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between border-b border-paper-line last:border-0 pb-1">
      <span className="text-ink-muted">{k}</span>
      <span className="font-mono">{v}</span>
    </div>
  );
}

import Link from "next/link";
import { getBenchmarkNames, getLeaderboard } from "@/lib/queries";
import { fmtElo, fmtPct, modelHref } from "@/lib/format";

export const revalidate = 1800;

type Props = { searchParams: Promise<{ b?: string }> };

const BENCH_LABELS: Record<string, string> = {
  "arena-elo":          "LMSYS Chatbot Arena Elo",
  "aa-intelligence":    "Artificial Analysis Intelligence Index",
  "aa-output-tps":      "Output tokens / second (AA)",
  "mmlu":               "MMLU",
  "gpqa":               "GPQA Diamond",
  "humaneval":          "HumanEval",
  "swe-bench-verified": "SWE-bench Verified",
  "math":               "MATH",
};

const DEFAULT = "arena-elo";

export default async function BenchmarksPage({ searchParams }: Props) {
  const { b } = await searchParams;
  const names: string[] = await getBenchmarkNames().catch(() => []);
  const active: string | undefined =
    b && names.includes(b) ? b : (names.includes(DEFAULT) ? DEFAULT : names[0]);
  const rows = active ? await getLeaderboard(active, 50).catch(() => []) : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Benchmarks</h1>
        <p className="text-ink-muted">Cross-vendor leaderboards. Click a benchmark to switch.</p>
      </div>

      <nav className="flex flex-wrap gap-2">
        {names.map((n) => (
          <Link
            key={n}
            href={`/benchmarks?b=${encodeURIComponent(n)}`}
            className={`px-3 py-1.5 text-xs rounded border ${
              n === active
                ? "bg-ink text-paper border-ink"
                : "bg-white border-paper-line hover:border-ink"
            }`}
          >
            {BENCH_LABELS[n] ?? n}
          </Link>
        ))}
        {names.length === 0 && <p className="text-sm text-ink-muted">No benchmark data yet.</p>}
      </nav>

      {active && (
        <div className="overflow-x-auto border border-paper-line dark:border-ink-line rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-paper-panel dark:bg-ink-soft text-left text-xs uppercase tracking-wider text-ink-muted">
              <tr>
                <th className="px-3 py-2 w-12">#</th>
                <th className="px-3 py-2">Model</th>
                <th className="px-3 py-2">Vendor</th>
                <th className="px-3 py-2 num">Score</th>
                <th className="px-3 py-2">Source</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.model_id} className="border-t border-paper-line dark:border-ink-line hover:bg-paper-panel/60 dark:hover:bg-ink-soft/60">
                  <td className="px-3 py-2 text-ink-muted font-mono">{i + 1}</td>
                  <td className="px-3 py-2">
                    <Link href={modelHref(r.model_id)} className="hover:text-accent">{r.name}</Link>
                  </td>
                  <td className="px-3 py-2">{r.vendor_name}</td>
                  <td className="px-3 py-2 num font-mono">
                    {r.score_unit === "pct" ? fmtPct(r.score) :
                     r.score_unit === "elo" ? fmtElo(r.score) :
                     r.score.toFixed(1)}
                  </td>
                  <td className="px-3 py-2 text-xs text-ink-muted">{r.source}</td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr><td colSpan={5} className="px-3 py-8 text-center text-ink-muted">No data for this benchmark.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

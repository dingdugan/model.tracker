import Link from "next/link";
import { Badge } from "@/components/Badge";
import { getModels } from "@/lib/queries";
import { countryFlag, fmtPrice, fmtTokens, modelHref } from "@/lib/format";

export const revalidate = 1800;

export default async function PricingPage() {
  const models = await getModels().catch(() => []);
  const priced = models
    .filter((m) => m.input_per_mtok != null || m.output_per_mtok != null)
    .filter((m) => m.status === "active" || m.status === "preview")
    .sort((a, b) => (a.input_per_mtok ?? Infinity) - (b.input_per_mtok ?? Infinity));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Pricing comparison</h1>
        <p className="text-ink-muted">USD per million tokens. Sorted by input price (ascending).</p>
      </div>

      <div className="overflow-x-auto border border-paper-line dark:border-ink-line rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-paper-panel dark:bg-ink-soft text-left text-xs uppercase tracking-wider text-ink-muted">
            <tr>
              <th className="px-3 py-2 w-12">#</th>
              <th className="px-3 py-2">Model</th>
              <th className="px-3 py-2">Vendor</th>
              <th className="px-3 py-2 num">Context</th>
              <th className="px-3 py-2 num">Input</th>
              <th className="px-3 py-2 num">Output</th>
              <th className="px-3 py-2 num">Cached input</th>
              <th className="px-3 py-2 num">Blended (3:1)</th>
            </tr>
          </thead>
          <tbody>
            {priced.map((m, i) => {
              const blended = blendedPrice(m.input_per_mtok, m.output_per_mtok);
              return (
                <tr key={m.id} className="border-t border-paper-line dark:border-ink-line hover:bg-paper-panel/60 dark:hover:bg-ink-soft/60">
                  <td className="px-3 py-2 text-ink-muted font-mono">{i + 1}</td>
                  <td className="px-3 py-2">
                    <Link href={modelHref(m.id)} className="hover:text-accent">{m.name}</Link>
                    {m.is_open_weight && <Badge tone="ok">open</Badge>}
                  </td>
                  <td className="px-3 py-2">
                    <span className="mr-1.5">{countryFlag(m.vendor_country)}</span>
                    {m.vendor_name}
                  </td>
                  <td className="px-3 py-2 num font-mono">{fmtTokens(m.context_window)}</td>
                  <td className="px-3 py-2 num font-mono">{fmtPrice(m.input_per_mtok)}</td>
                  <td className="px-3 py-2 num font-mono">{fmtPrice(m.output_per_mtok)}</td>
                  <td className="px-3 py-2 num font-mono">{fmtPrice(m.cached_input_per_mtok)}</td>
                  <td className="px-3 py-2 num font-mono">{blended != null ? fmtPrice(blended) : "—"}</td>
                </tr>
              );
            })}
            {priced.length === 0 && (
              <tr><td colSpan={8} className="px-3 py-8 text-center text-ink-muted">No pricing data yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-ink-muted">
        Blended assumes 3 input tokens per 1 output token — a rough proxy for typical chat usage.
      </p>
    </div>
  );
}

function blendedPrice(input: number | null, output: number | null): number | null {
  if (input == null || output == null) return null;
  return (input * 3 + output * 1) / 4;
}

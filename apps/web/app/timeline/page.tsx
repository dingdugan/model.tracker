import Link from "next/link";
import { Badge } from "@/components/Badge";
import { getModels } from "@/lib/queries";
import { countryFlag, fmtDate, modelHref } from "@/lib/format";

export const revalidate = 1800;

export default async function TimelinePage() {
  const models = await getModels().catch(() => []);
  const dated = models
    .filter((m) => m.release_date)
    .sort((a, b) => (b.release_date ?? "").localeCompare(a.release_date ?? ""));

  // Group by month
  const byMonth = new Map<string, typeof dated>();
  for (const m of dated) {
    const month = (m.release_date ?? "").slice(0, 7);
    if (!byMonth.has(month)) byMonth.set(month, []);
    byMonth.get(month)!.push(m);
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Release timeline</h1>
        <p className="text-ink-muted">Models with public release dates, newest first.</p>
      </div>

      <div className="space-y-0">
        {Array.from(byMonth.entries()).map(([month, rows], i, arr) => (
          <div key={month} className="flex gap-5">
            {/* dot + line column */}
            <div className="flex flex-col items-center shrink-0 w-3">
              <div className="w-3 h-3 rounded-full bg-accent shrink-0 mt-1" />
              {i < arr.length - 1 && <div className="w-px flex-1 bg-paper-line dark:bg-ink-line mt-1" />}
            </div>
            {/* content column */}
            <div className="pb-8 flex-1 min-w-0">
              <h2 className="text-sm font-mono uppercase tracking-wider text-ink-muted mb-3 mt-0.5">{month}</h2>
              <ul className="space-y-3">
                {rows.map((m) => (
                  <li key={m.id} className="flex flex-wrap items-baseline gap-2 text-sm">
                    <span className="font-mono text-ink-muted">{fmtDate(m.release_date)}</span>
                    <span>{countryFlag(m.vendor_country)}</span>
                    <span className="font-medium">{m.vendor_name}</span>
                    <span className="text-ink-muted">released</span>
                    <Link href={modelHref(m.id)} className="hover:text-accent">{m.name}</Link>
                    {m.is_open_weight && <Badge tone="ok">open</Badge>}
                    {m.status === "preview" && <Badge tone="warn">preview</Badge>}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
        {dated.length === 0 && <p className="text-sm text-ink-muted">No dated releases yet.</p>}
      </div>
    </div>
  );
}

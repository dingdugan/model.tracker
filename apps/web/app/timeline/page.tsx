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

      <div className="relative pl-6 border-l border-paper-line dark:border-ink-line">
        {Array.from(byMonth.entries()).map(([month, rows]) => (
          <section key={month} className="mb-10 relative">
            <div className="absolute -left-[7px] top-1.5 w-3 h-3 rounded-full bg-accent" />
            <h2 className="text-sm font-mono uppercase tracking-wider text-ink-muted mb-3">{month}</h2>
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
          </section>
        ))}
        {dated.length === 0 && <p className="text-sm text-ink-muted">No dated releases yet.</p>}
      </div>
    </div>
  );
}

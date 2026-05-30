import Link from "next/link";
import { getChangelog } from "@/lib/queries";
import { fmtDate, fmtPrice, fmtPctChange, modelHref } from "@/lib/format";
import { Badge } from "@/components/Badge";

export const revalidate = 300;

export default async function ChangelogPage() {
  const days = await getChangelog(60).catch(() => []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Changelog</h1>
        <p className="text-sm text-ink-muted mt-1">Every detected change to the model landscape, day by day.</p>
      </div>

      {days.length === 0 && (
        <div className="border border-paper-line dark:border-ink-line rounded-lg py-16 text-center text-ink-muted text-sm">
          No changes recorded yet.
        </div>
      )}

      <div className="space-y-4">
        {days.map((day) => {
          const hasContent = day.newModels.length > 0 || day.priceChanges.length > 0;
          return (
            <div key={day.date} className="border border-paper-line dark:border-ink-line rounded-lg overflow-hidden">
              {/* Date header */}
              <div className="flex items-center gap-3 px-5 py-3 bg-paper-panel dark:bg-ink-soft border-b border-paper-line dark:border-ink-line">
                <span className="font-mono text-sm font-semibold">{fmtDate(day.date)}</span>
                <div className="flex gap-1.5 ml-1">
                  {day.newModels.length > 0 && (
                    <Badge tone="accent">{day.newModels.length} new</Badge>
                  )}
                  {day.priceChanges.length > 0 && (
                    <Badge tone="warn">{day.priceChanges.length} price {day.priceChanges.length === 1 ? "change" : "changes"}</Badge>
                  )}
                </div>
              </div>

              <div className="p-5 space-y-5 text-sm">
                {!hasContent && (
                  <p className="text-ink-muted">No changes.</p>
                )}

                {/* New models */}
                {day.newModels.length > 0 && (
                  <div>
                    <h3 className="text-[10px] uppercase tracking-wider text-ink-muted mb-2 font-mono">New models</h3>
                    <ul className="space-y-1.5">
                      {day.newModels.map((m) => (
                        <li key={m.id} className="flex items-center gap-2">
                          <Link href={modelHref(m.id)} className="font-medium hover:text-accent">
                            {m.name}
                          </Link>
                          <span className="text-ink-muted text-xs">by {m.vendor}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Price changes */}
                {day.priceChanges.length > 0 && (
                  <div>
                    <h3 className="text-[10px] uppercase tracking-wider text-ink-muted mb-2 font-mono">Price changes</h3>
                    <div className="divide-y divide-paper-line dark:divide-ink-line border border-paper-line dark:border-ink-line rounded">
                      {day.priceChanges.map((c, i) => {
                        const inputChanged  = c.input_old  !== c.input_new;
                        const outputChanged = c.output_old !== c.output_new;
                        return (
                          <div key={`${c.model_id}-${i}`} className="px-4 py-3 flex flex-wrap gap-x-6 gap-y-1">
                            <Link href={modelHref(c.model_id)} className="font-medium hover:text-accent shrink-0">
                              {c.model_name}
                            </Link>
                            {inputChanged && (
                              <PriceCell label="in" old={c.input_old} new_={c.input_new} />
                            )}
                            {outputChanged && (
                              <PriceCell label="out" old={c.output_old} new_={c.output_new} />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PriceCell({ label, old, new_ }: { label: string; old: number | null; new_: number | null }) {
  const pct = fmtPctChange(old, new_);
  const up  = (new_ ?? 0) > (old ?? 0);
  return (
    <span className="flex items-center gap-1.5 text-xs font-mono">
      <span className="text-ink-muted uppercase">{label}</span>
      <span className="text-ink-muted">{fmtPrice(old)}</span>
      <span className="text-ink-muted">→</span>
      <span className={up ? "text-red-600" : "text-emerald-700"}>{fmtPrice(new_)}</span>
      <span className={`text-[10px] ${up ? "text-red-500" : "text-emerald-600"}`}>({pct})</span>
    </span>
  );
}

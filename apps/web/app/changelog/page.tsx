import Link from "next/link";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { getRecentSnapshots } from "@/lib/queries";
import { fmtDate, fmtPrice, modelHref } from "@/lib/format";

export const revalidate = 1800;

export default async function ChangelogPage() {
  const snapshots = await getRecentSnapshots(60).catch(() => []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Changelog</h1>
        <p className="text-ink-muted">Every detected change to the model landscape, day by day.</p>
      </div>

      <div className="space-y-5">
        {snapshots.map((s) => {
          const empty =
            !(s.new_models?.length || s.price_changes?.length || s.status_changes?.length || s.bench_changes?.length);
          return (
            <Card key={s.snapshot_date}>
              <div className="flex items-center justify-between px-5 py-3 border-b border-paper-line dark:border-ink-line">
                <h2 className="font-mono text-sm">{fmtDate(s.snapshot_date)}</h2>
                <div className="flex gap-2 text-[10px]">
                  {s.new_models?.length    ? <Badge tone="accent">{s.new_models.length} new</Badge> : null}
                  {s.price_changes?.length ? <Badge tone="warn">{s.price_changes.length} price</Badge> : null}
                  {s.status_changes?.length ? <Badge tone="muted">{s.status_changes.length} status</Badge> : null}
                </div>
              </div>
              <div className="p-5 text-sm">
                {empty && <p className="text-ink-muted">No changes.</p>}
                {s.new_models?.length ? (
                  <div className="mb-4">
                    <h3 className="text-xs uppercase tracking-wider text-ink-muted mb-1.5">New models</h3>
                    <ul className="space-y-1">
                      {s.new_models.map((m) => (
                        <li key={m.id}>
                          <Link href={modelHref(m.id)} className="hover:text-accent">{m.name}</Link>
                          <span className="text-ink-muted"> · {m.vendor}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {s.price_changes?.length ? (
                  <div className="mb-4">
                    <h3 className="text-xs uppercase tracking-wider text-ink-muted mb-1.5">Price changes</h3>
                    <ul className="space-y-1">
                      {s.price_changes.map((c, i) => (
                        <li key={`${c.model_id}-${i}`} className="flex justify-between gap-2">
                          <Link href={modelHref(c.model_id)} className="hover:text-accent">{c.model_id.split("/")[1]}</Link>
                          <span className="text-ink-muted font-mono">
                            {c.field}: {fmtPrice(c.old)} → {fmtPrice(c.new)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {s.status_changes?.length ? (
                  <div>
                    <h3 className="text-xs uppercase tracking-wider text-ink-muted mb-1.5">Status changes</h3>
                    <ul className="space-y-1">
                      {s.status_changes.map((c) => (
                        <li key={c.id} className="flex justify-between gap-2">
                          <Link href={modelHref(c.id)} className="hover:text-accent">{c.id.split("/")[1]}</Link>
                          <span className="text-ink-muted font-mono">{c.old_status} → {c.new_status}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            </Card>
          );
        })}
        {snapshots.length === 0 && (
          <Card><div className="p-8 text-center text-ink-muted">No snapshots yet.</div></Card>
        )}
      </div>
    </div>
  );
}

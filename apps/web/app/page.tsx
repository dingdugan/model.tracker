import Link from "next/link";
import { Card, CardHeader } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { getModels, getLatestSnapshot, getLeaderboard, getRecentSnapshots } from "@/lib/queries";
import { countryFlag, fmtDate, fmtElo, fmtPrice, fmtTokens, modelHref } from "@/lib/format";

export const revalidate = 1800;

export default async function HomePage() {
  const [models, latest, snapshots, arenaTop] = await Promise.all([
    safe(() => getModels()),
    safe(() => getLatestSnapshot()),
    safe(() => getRecentSnapshots(7)),
    safe(() => getLeaderboard("arena-elo", 8)),
  ]);

  const active = models.filter((m) => m.status === "active");
  const cheapestActive = [...active]
    .filter((m) => m.input_per_mtok != null && m.input_per_mtok > 0)
    .sort((a, b) => (a.input_per_mtok ?? Infinity) - (b.input_per_mtok ?? Infinity))
    .slice(0, 6);

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Global AI model tracker</h1>
          <p className="text-ink-muted mt-1">
            Daily-updated catalogue of LLM releases, pricing, and benchmark performance across 14 vendors.
          </p>
        </div>
        <div className="flex gap-6 text-sm">
          <Stat label="Vendors"   value={String(latest?.vendors_count ?? new Set(models.map(m=>m.vendor_id)).size)} />
          <Stat label="Models"    value={String(latest?.models_count ?? models.length)} />
          <Stat label="Active"    value={String(active.length)} />
          <Stat label="Snapshot"  value={fmtDate(latest?.snapshot_date)} />
        </div>
      </div>

      {/* Today's changes */}
      <Card>
        <CardHeader title="Latest changes" subtitle={latest ? fmtDate(latest.snapshot_date) : "No snapshot yet"} />
        <div className="grid md:grid-cols-3 gap-px bg-paper-line dark:bg-ink-line">
          <Pane title="New models" empty="No new models">
            {latest?.new_models?.slice(0, 8).map((m) => (
              <li key={m.id} className="flex justify-between gap-2">
                <Link href={modelHref(m.id)} className="truncate hover:text-accent">{m.name}</Link>
                <span className="text-ink-muted shrink-0">{m.vendor}</span>
              </li>
            ))}
          </Pane>
          <Pane title="Price changes" empty="No price changes">
            {latest?.price_changes?.slice(0, 8).map((c, i) => (
              <li key={`${c.model_id}-${i}`} className="flex justify-between gap-2">
                <Link href={modelHref(c.model_id)} className="truncate hover:text-accent">{c.model_id.split("/")[1]}</Link>
                <span className="text-ink-muted shrink-0 font-mono">
                  {fmtPrice(c.old)} → {fmtPrice(c.new)}
                </span>
              </li>
            ))}
          </Pane>
          <Pane title="Status changes" empty="No status changes">
            {latest?.status_changes?.slice(0, 8).map((c, i) => (
              <li key={`${c.id}-${i}`} className="flex justify-between gap-2">
                <Link href={modelHref(c.id)} className="truncate hover:text-accent">{c.id.split("/")[1]}</Link>
                <span className="text-ink-muted font-mono">{c.old_status} → {c.new_status}</span>
              </li>
            ))}
          </Pane>
        </div>
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Arena top */}
        <Card>
          <CardHeader title="Arena top 8" subtitle="LMSYS Chatbot Arena Elo"
            right={<Link href="/benchmarks?b=arena-elo" className="text-xs text-ink-muted hover:text-accent">all →</Link>}/>
          <ol className="divide-y divide-paper-line dark:divide-ink-line">
            {arenaTop.length === 0 && <li className="px-5 py-4 text-sm text-ink-muted">No Arena data yet.</li>}
            {arenaTop.map((row, idx) => (
              <li key={row.model_id} className="px-5 py-3 flex items-center gap-3 text-sm">
                <span className="w-6 text-right text-ink-muted font-mono">{idx + 1}</span>
                <Link href={modelHref(row.model_id)} className="flex-1 truncate hover:text-accent">
                  {row.name}
                </Link>
                <span className="text-xs text-ink-muted">{row.vendor_name}</span>
                <span className="font-mono w-12 text-right">{fmtElo(row.score)}</span>
              </li>
            ))}
          </ol>
        </Card>

        {/* Cheapest */}
        <Card>
          <CardHeader title="Cheapest active models" subtitle="By input price"
            right={<Link href="/pricing" className="text-xs text-ink-muted hover:text-accent">all →</Link>}/>
          <ol className="divide-y divide-paper-line dark:divide-ink-line">
            {cheapestActive.map((m) => (
              <li key={m.id} className="px-5 py-3 flex items-center gap-3 text-sm">
                <span>{countryFlag(m.vendor_country)}</span>
                <Link href={modelHref(m.id)} className="flex-1 truncate hover:text-accent">{m.name}</Link>
                <span className="text-xs text-ink-muted hidden sm:inline">{fmtTokens(m.context_window)} ctx</span>
                <span className="font-mono w-20 text-right">{fmtPrice(m.input_per_mtok)}/Mtok</span>
              </li>
            ))}
          </ol>
        </Card>
      </div>

      {/* 7-day activity */}
      <Card>
        <CardHeader title="Last 7 days" />
        <ul className="divide-y divide-paper-line dark:divide-ink-line">
          {snapshots.length === 0 && <li className="px-5 py-4 text-sm text-ink-muted">No history yet.</li>}
          {snapshots.map((s) => {
            const total = (s.new_models?.length ?? 0) + (s.price_changes?.length ?? 0) + (s.status_changes?.length ?? 0);
            return (
              <li key={s.snapshot_date} className="px-5 py-3 flex items-center gap-4 text-sm">
                <span className="font-mono text-ink-muted w-24">{fmtDate(s.snapshot_date)}</span>
                <span className="flex-1 truncate">
                  {s.new_models?.length ? `${s.new_models.length} new · ` : ""}
                  {s.price_changes?.length ? `${s.price_changes.length} price · ` : ""}
                  {s.status_changes?.length ? `${s.status_changes.length} status` : ""}
                  {!total && <span className="text-ink-muted">no changes</span>}
                </span>
                <Badge tone={total ? "accent" : "muted"}>{total}</Badge>
              </li>
            );
          })}
        </ul>
      </Card>
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

function Pane({ title, children, empty }: { title: string; children: React.ReactNode; empty: string }) {
  const arr = Array.isArray(children) ? children.filter(Boolean) : children;
  const isEmpty = !arr || (Array.isArray(arr) && arr.length === 0);
  return (
    <div className="bg-white dark:bg-ink-soft p-5">
      <h3 className="text-xs uppercase tracking-wider text-ink-muted mb-3">{title}</h3>
      {isEmpty ? (
        <p className="text-sm text-ink-muted">{empty}</p>
      ) : (
        <ul className="space-y-1.5 text-sm">{children}</ul>
      )}
    </div>
  );
}

async function safe<T>(fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch {
    // Empty placeholder; each call-site treats null/[] uniformly.
    return [] as unknown as T;
  }
}

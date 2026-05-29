import Link from "next/link";
import {
  getDiscoveryCandidates,
  getPendingChanges,
  getRecentIssues,
  getStalePrices,
} from "@/lib/queries";
import { fmtDate, modelHref } from "@/lib/format";
import { Badge } from "@/components/Badge";

export const revalidate = 1800;

export const metadata = {
  title: "Data Health — model.tracker",
  description: "Pipeline transparency: discovered models, quarantined values, stale prices, scrape issues.",
};

export default async function HealthPage() {
  const [candidates, pending, issues, stale] = await Promise.all([
    getDiscoveryCandidates().catch(() => []),
    getPendingChanges().catch(() => []),
    getRecentIssues().catch(() => []),
    getStalePrices(30).catch(() => []),
  ]);

  const tracked = candidates.filter((c) => c.vendor_guess);
  const untracked = candidates.filter((c) => !c.vendor_guess);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Data health</h1>
        <p className="text-sm text-ink-muted mt-1">
          What the pipeline knows it doesn&apos;t know. Surfaced on purpose — a model we
          fail to track or a value we&apos;re unsure of shows up here instead of being
          silently dropped.
        </p>
      </div>

      {/* Stat row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="Discovered (unrecognized)" value={candidates.length} tone={candidates.length ? "accent" : "ok"} />
        <Stat label="Quarantined values" value={pending.length} tone={pending.length ? "warn" : "ok"} />
        <Stat label="Stale prices (>30d)" value={stale.length} tone={stale.length ? "warn" : "ok"} />
        <Stat label="Recent scrape issues" value={issues.length} tone={issues.length ? "warn" : "ok"} />
      </div>

      {/* Quarantined values */}
      <Section
        title="Quarantined values"
        subtitle="A scraped value looked anomalous; the last-known-good value stays live until it's confirmed or reviewed."
      >
        {pending.length === 0 ? (
          <Empty>No quarantined values — all scraped data passed the anomaly gate.</Empty>
        ) : (
          <div className="divide-y divide-paper-line dark:divide-ink-line border border-paper-line dark:border-ink-line rounded-lg">
            {pending.map((p, i) => (
              <div key={i} className="px-4 py-3 flex flex-wrap items-baseline gap-x-4 gap-y-1 text-sm">
                <Link href={modelHref(p.model_id)} className="font-medium hover:text-accent">{p.model_id}</Link>
                <span className="font-mono text-xs text-ink-muted">{p.field}</span>
                <span className="font-mono text-xs">
                  {fmtNum(p.prior_value)} <span className="text-ink-muted">→</span> {fmtNum(p.proposed_value)}
                </span>
                <span className="text-xs text-ink-muted">{p.reason}</span>
                <Badge tone="muted">held {p.occurrences}×</Badge>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Discovered models */}
      <Section
        title="Discovered models (not yet tracked)"
        subtitle="Names seen on vendor APIs or leaderboards that don't match any model in the catalog."
      >
        {candidates.length === 0 ? (
          <Empty>Nothing undiscovered — every name we saw maps to a tracked model.</Empty>
        ) : (
          <div className="space-y-4">
            {tracked.length > 0 && (
              <div>
                <h3 className="text-[11px] uppercase tracking-wider text-ink-muted mb-2 font-mono">
                  ⭐ From vendors we track ({tracked.length})
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {tracked.map((c, i) => (
                    <span key={i} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-accent/40 bg-accent/5 text-xs font-mono">
                      {c.reported_name}
                      <span className="text-ink-muted">{c.vendor_guess}</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
            {untracked.length > 0 && (
              <div>
                <h3 className="text-[11px] uppercase tracking-wider text-ink-muted mb-2 font-mono">
                  Other / untracked vendors ({untracked.length})
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {untracked.map((c, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-full border border-paper-line dark:border-ink-line text-xs font-mono text-ink-muted">
                      {c.reported_name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Section>

      {/* Stale prices */}
      <Section
        title="Stale prices"
        subtitle="Active models whose price hasn't refreshed in over 30 days."
      >
        {stale.length === 0 ? (
          <Empty>All tracked prices refreshed within the last 30 days.</Empty>
        ) : (
          <div className="divide-y divide-paper-line dark:divide-ink-line border border-paper-line dark:border-ink-line rounded-lg">
            {stale.map((m) => (
              <div key={m.id} className="px-4 py-2.5 flex items-center gap-3 text-sm">
                <Link href={modelHref(m.id)} className="font-medium hover:text-accent">{m.name}</Link>
                <span className="text-ink-muted text-xs">{m.vendor_name}</span>
                <span className="ml-auto font-mono text-xs text-ink-muted">
                  {m.price_effective_date ? fmtDate(m.price_effective_date) : "—"}
                </span>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Scrape issues */}
      <Section
        title="Recent scrape issues"
        subtitle="Errors and drift warnings from recent runs (operational detail lives in GitHub issues)."
      >
        {issues.length === 0 ? (
          <Empty>No recent scrape issues.</Empty>
        ) : (
          <div className="divide-y divide-paper-line dark:divide-ink-line border border-paper-line dark:border-ink-line rounded-lg">
            {issues.map((e, i) => (
              <div key={i} className="px-4 py-2.5 flex items-center gap-3 text-sm">
                <Badge tone={e.stage === "drift" ? "warn" : "muted"}>{e.stage}</Badge>
                <span className="font-mono text-xs">{e.vendor_id ?? e.benchmark ?? "—"}</span>
                {e.error_class && <span className="text-xs text-ink-muted">{e.error_class}</span>}
                <span className="ml-auto font-mono text-xs text-ink-muted">{fmtDate(e.occurred_at?.slice(0, 10))}</span>
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone: "ok" | "warn" | "accent" }) {
  const color =
    tone === "warn" ? "text-amber-600" : tone === "accent" ? "text-accent" : "text-emerald-700";
  return (
    <div className="border border-paper-line dark:border-ink-line rounded-lg px-4 py-3">
      <div className="text-[10px] uppercase tracking-wider text-ink-muted">{label}</div>
      <div className={`font-mono text-2xl font-semibold mt-0.5 ${color}`}>{value}</div>
    </div>
  );
}

function Section({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
        <p className="text-xs text-ink-muted mt-0.5">{subtitle}</p>
      </div>
      {children}
    </section>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return (
    <div className="border border-paper-line dark:border-ink-line rounded-lg py-8 text-center text-ink-muted text-sm">
      {children}
    </div>
  );
}

function fmtNum(v: number | null): string {
  return v == null ? "—" : String(v);
}

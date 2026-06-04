"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { ModelOverview } from "@/lib/types";
import { Badge } from "@/components/Badge";
import { countryFlag, fmtElo, fmtPrice, fmtTokens, modelHref } from "@/lib/format";

type SortKey =
  | "name" | "vendor_name" | "release_date" | "context_window"
  | "input_per_mtok" | "output_per_mtok" | "arena_elo" | "parameters_b";

const ELO_SUBS = [
  { key: "arena_elo_coding" as const, label: "Coding" },
  { key: "arena_elo_vision" as const, label: "Vision" },
];

type WeightFilter = "all" | "open" | "closed";

export function ModelsTable({ models }: { models: ModelOverview[] }) {
  const [q, setQ]                   = useState("");
  const [vendor, setVendor]         = useState<string>("all");
  const [weight, setWeight]         = useState<WeightFilter>("all");
  const [sortKey, setSortKey]       = useState<SortKey>("arena_elo");
  const [sortDir, setSortDir]       = useState<"asc" | "desc">("desc");
  const [eloExpanded, setEloExpanded] = useState(false);

  // Derive vendor list from data, keeping display order consistent
  const vendors = useMemo(() => {
    const map = new Map<string, { id: string; name: string; country: string }>();
    models.forEach((m) => {
      if (!map.has(m.vendor_id)) map.set(m.vendor_id, { id: m.vendor_id, name: m.vendor_name, country: m.vendor_country });
    });
    return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [models]);

  // Summary stats
  const stats = useMemo(() => {
    const active = models.filter((m) => m.status === "active" || m.status === "preview");
    const withPrice = active.filter((m) => m.input_per_mtok != null);
    const cheapest = withPrice.reduce<ModelOverview | null>(
      (acc, m) => (!acc || (m.input_per_mtok ?? Infinity) < (acc.input_per_mtok ?? Infinity)) ? m : acc,
      null,
    );
    const topElo = active.reduce<ModelOverview | null>(
      (acc, m) => (!acc || (m.arena_elo ?? -Infinity) > (acc.arena_elo ?? -Infinity)) ? m : acc,
      null,
    );
    return { total: active.length, cheapest, topElo };
  }, [models]);

  const filtered = useMemo(() => {
    return models.filter((m) => {
      if (m.status === "retired") return false;
      if (vendor !== "all" && m.vendor_id !== vendor) return false;
      if (weight === "open"   && !m.is_open_weight) return false;
      if (weight === "closed" &&  m.is_open_weight) return false;
      if (q) {
        const needle = q.toLowerCase();
        if (!m.name.toLowerCase().includes(needle) && !m.vendor_name.toLowerCase().includes(needle)) return false;
      }
      return true;
    });
  }, [models, vendor, weight, q]);

  const sorted = useMemo(() => {
    const dir = sortDir === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const va = (a as any)[sortKey] ?? null;
      const vb = (b as any)[sortKey] ?? null;
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (typeof va === "number") return (va - vb) * dir;
      return String(va).localeCompare(String(vb)) * dir;
    });
  }, [filtered, sortKey, sortDir]);

  function toggleSort(k: SortKey) {
    if (sortKey === k) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(k); setSortDir(k === "name" || k === "vendor_name" ? "asc" : "desc"); }
  }

  return (
    <div className="space-y-4">
      {/* Stats bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pb-1">
        <StatBox label="Models tracked" value={String(stats.total)} />
        <StatBox
          label="Cheapest input"
          value={stats.cheapest ? fmtPrice(stats.cheapest.input_per_mtok) : "—"}
          sub={stats.cheapest?.name}
        />
        <StatBox
          label="Top Arena ELO"
          value={stats.topElo ? fmtElo(stats.topElo.arena_elo) : "—"}
          sub={stats.topElo?.name}
        />
        <StatBox label="Vendors" value={String(vendors.length)} />
      </div>

      {/* Filter row */}
      <div className="space-y-2">
        {/* Vendor chips — horizontally scrollable */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          <Chip active={vendor === "all"} onClick={() => setVendor("all")}>ALL</Chip>
          {vendors.map((v) => (
            <Chip key={v.id} active={vendor === v.id} onClick={() => setVendor(v.id)}>
              {countryFlag(v.country)} {v.name}
            </Chip>
          ))}
        </div>

        {/* Type + search */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex gap-1">
            {(["all", "open", "closed"] as WeightFilter[]).map((w) => (
              <Chip key={w} active={weight === w} onClick={() => setWeight(w)} small>
                {w === "all" ? "All" : w === "open" ? "Open weight" : "Closed"}
              </Chip>
            ))}
          </div>
          <div className="ml-auto flex items-center gap-3">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search…"
              className="px-3 py-1 text-sm border border-paper-line rounded bg-white dark:bg-ink-soft dark:border-ink-line w-40"
            />
            <span className="text-xs font-mono text-ink-muted whitespace-nowrap">
              {sorted.length} / {models.filter(m => m.status !== "retired").length}
            </span>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-paper-line dark:border-ink-line rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-paper-panel dark:bg-ink-soft text-left text-[11px] uppercase tracking-wider text-ink-muted">
            <tr>
              <Th onClick={() => toggleSort("name")} active={sortKey === "name"} dir={sortDir}>Model</Th>
              <Th onClick={() => toggleSort("vendor_name")} active={sortKey === "vendor_name"} dir={sortDir}>Vendor</Th>
              <Th onClick={() => toggleSort("input_per_mtok")} active={sortKey === "input_per_mtok"} dir={sortDir} num>In $/Mtok</Th>
              <Th onClick={() => toggleSort("output_per_mtok")} active={sortKey === "output_per_mtok"} dir={sortDir} num>Out $/Mtok</Th>
              <Th onClick={() => toggleSort("context_window")} active={sortKey === "context_window"} dir={sortDir} num>Context</Th>
              <Th onClick={() => toggleSort("arena_elo")} active={sortKey === "arena_elo"} dir={sortDir} num
                expand={{ expanded: eloExpanded, onToggle: () => setEloExpanded(e => !e) }}>
                Arena ELO
              </Th>
              {eloExpanded && ELO_SUBS.map(s => (
                <Th key={s.key} num>{s.label}</Th>
              ))}
              <Th onClick={() => toggleSort("parameters_b")} active={sortKey === "parameters_b"} dir={sortDir} num>Params</Th>
              <Th>Modality</Th>
              <Th>License</Th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((m) => (
              <tr
                key={m.id}
                className="border-t border-paper-line dark:border-ink-line hover:bg-paper-panel/60 dark:hover:bg-ink-soft/60 group"
              >
                <td className="px-3 py-2">
                  <Link href={modelHref(m.id)} className="hover:text-accent font-medium">
                    {m.name}
                  </Link>
                  <span className="ml-1.5 inline-flex gap-1">
                    {m.is_open_weight && <Badge tone="ok">open</Badge>}
                    {m.status === "preview"    && <Badge tone="warn">preview</Badge>}
                    {m.status === "deprecated" && <Badge tone="muted">deprecated</Badge>}
                    {m.auto_discovered && <Badge tone="muted">auto</Badge>}
                  </span>
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-ink-muted">
                  <span className="mr-1">{countryFlag(m.vendor_country)}</span>
                  {m.vendor_name}
                </td>
                <td className="px-3 py-2 text-right font-mono">{fmtPrice(m.input_per_mtok)}</td>
                <td className="px-3 py-2 text-right font-mono">{fmtPrice(m.output_per_mtok)}</td>
                <td className="px-3 py-2 text-right font-mono">{fmtTokens(m.context_window)}</td>
                <td className="px-3 py-2 text-right font-mono">{fmtElo(m.arena_elo)}</td>
                {eloExpanded && ELO_SUBS.map(s => (
                  <td key={s.key} className="px-3 py-2 text-right font-mono text-ink-muted">{fmtElo(m[s.key])}</td>
                ))}
                <td className="px-3 py-2 text-right font-mono text-ink-muted">
                  {m.parameters_b != null ? `${m.parameters_b}B` : "—"}
                </td>
                <td className="px-3 py-2 whitespace-nowrap">
                  {m.modalities?.length ? (
                    <span className="text-xs font-mono text-ink-muted">{m.modalities.join(" · ")}</span>
                  ) : (
                    <span className="text-xs text-ink-muted/50">—</span>
                  )}
                </td>
                <td className="px-3 py-2">
                  {m.license ? (
                    <span className="text-xs font-mono text-ink-muted">{m.license}</span>
                  ) : (
                    <span className="text-xs text-ink-muted/50">—</span>
                  )}
                </td>
              </tr>
            ))}
            {sorted.length === 0 && (
              <tr>
                <td colSpan={9 + (eloExpanded ? ELO_SUBS.length : 0)} className="px-3 py-10 text-center text-ink-muted">No models match.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatBox({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="border border-paper-line dark:border-ink-line rounded-lg px-4 py-3">
      <div className="text-[10px] uppercase tracking-wider text-ink-muted">{label}</div>
      <div className="font-mono text-xl font-semibold mt-0.5">{value}</div>
      {sub && <div className="text-[11px] text-ink-muted truncate mt-0.5">{sub}</div>}
    </div>
  );
}

function Chip({
  children, active, onClick, small,
}: {
  children: React.ReactNode;
  active?: boolean;
  onClick?: () => void;
  small?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={[
        "shrink-0 rounded-full border font-mono transition-colors whitespace-nowrap",
        small ? "px-2.5 py-0.5 text-[11px]" : "px-3 py-1 text-xs",
        active
          ? "border-accent bg-accent text-white"
          : "border-paper-line dark:border-ink-line text-ink-muted hover:text-ink hover:border-ink-muted",
      ].join(" ")}
    >
      {children}
    </button>
  );
}

function Th({
  children, onClick, active, dir, num, expand,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  active?: boolean;
  dir?: "asc" | "desc";
  num?: boolean;
  expand?: { expanded: boolean; onToggle: () => void };
}) {
  return (
    <th
      onClick={onClick}
      className={[
        "px-3 py-2.5",
        num ? "text-right" : "",
        onClick ? "cursor-pointer select-none hover:text-ink" : "",
        active ? "text-ink" : "",
      ].join(" ")}
    >
      <span className="inline-flex items-center gap-1">
        {children}
        {active && <span>{dir === "asc" ? "↑" : "↓"}</span>}
        {expand && (
          <button
            onClick={(e) => { e.stopPropagation(); expand.onToggle(); }}
            className="text-[10px] text-ink-muted hover:text-accent border border-current rounded px-0.5 leading-tight"
            title={expand.expanded ? "Collapse sub-categories" : "Expand sub-categories"}
          >
            {expand.expanded ? "◂" : "▸"}
          </button>
        )}
      </span>
    </th>
  );
}

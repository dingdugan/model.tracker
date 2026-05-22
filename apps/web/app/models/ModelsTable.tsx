"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { ModelOverview } from "@/lib/types";
import { Badge } from "@/components/Badge";
import { countryFlag, fmtElo, fmtPrice, fmtTokens, modelHref } from "@/lib/format";

type SortKey = "name" | "vendor_name" | "release_date" | "context_window" | "input_per_mtok" | "output_per_mtok" | "arena_elo";

export function ModelsTable({ models }: { models: ModelOverview[] }) {
  const [q, setQ] = useState("");
  const [vendor, setVendor] = useState<string>("all");
  const [openOnly, setOpenOnly] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("active+preview");
  const [sortKey, setSortKey] = useState<SortKey>("arena_elo");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const vendors = useMemo(() => {
    const s = new Map<string, string>();
    models.forEach((m) => s.set(m.vendor_id, m.vendor_name));
    return Array.from(s.entries()).sort((a, b) => a[1].localeCompare(b[1]));
  }, [models]);

  const filtered = useMemo(() => {
    return models.filter((m) => {
      if (vendor !== "all" && m.vendor_id !== vendor) return false;
      if (openOnly && !m.is_open_weight) return false;
      if (statusFilter === "active" && m.status !== "active") return false;
      if (statusFilter === "active+preview" && !(m.status === "active" || m.status === "preview")) return false;
      if (q) {
        const needle = q.toLowerCase();
        if (!m.name.toLowerCase().includes(needle) && !m.vendor_name.toLowerCase().includes(needle)) return false;
      }
      return true;
    });
  }, [models, q, vendor, openOnly, statusFilter]);

  const sorted = useMemo(() => {
    const dir = sortDir === "asc" ? 1 : -1;
    const arr = [...filtered];
    arr.sort((a, b) => {
      const va = (a[sortKey] ?? null) as any;
      const vb = (b[sortKey] ?? null) as any;
      if (va == null && vb == null) return 0;
      if (va == null) return 1;       // nulls last
      if (vb == null) return -1;
      if (typeof va === "number" && typeof vb === "number") return (va - vb) * dir;
      return String(va).localeCompare(String(vb)) * dir;
    });
    return arr;
  }, [filtered, sortKey, sortDir]);

  function toggleSort(k: SortKey) {
    if (sortKey === k) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else { setSortKey(k); setSortDir(k === "name" || k === "vendor_name" ? "asc" : "desc"); }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search models or vendors…"
          className="px-3 py-1.5 text-sm border border-paper-line rounded bg-white dark:bg-ink-soft dark:border-ink-line w-56"
        />
        <select value={vendor} onChange={(e) => setVendor(e.target.value)}
          className="px-3 py-1.5 text-sm border border-paper-line rounded bg-white dark:bg-ink-soft dark:border-ink-line">
          <option value="all">All vendors</option>
          {vendors.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-1.5 text-sm border border-paper-line rounded bg-white dark:bg-ink-soft dark:border-ink-line">
          <option value="active+preview">Active + preview</option>
          <option value="active">Active only</option>
          <option value="all">Include deprecated</option>
        </select>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={openOnly} onChange={(e) => setOpenOnly(e.target.checked)} />
          Open-weight only
        </label>
        <span className="ml-auto text-xs font-mono text-ink-muted">{sorted.length} models</span>
      </div>

      <div className="overflow-x-auto border border-paper-line dark:border-ink-line rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-paper-panel dark:bg-ink-soft text-left text-xs uppercase tracking-wider text-ink-muted">
            <tr>
              <Th onClick={() => toggleSort("name")} active={sortKey === "name"} dir={sortDir}>Model</Th>
              <Th onClick={() => toggleSort("vendor_name")} active={sortKey === "vendor_name"} dir={sortDir}>Vendor</Th>
              <Th onClick={() => toggleSort("context_window")} active={sortKey === "context_window"} dir={sortDir} className="num">Context</Th>
              <Th className="num">Modalities</Th>
              <Th onClick={() => toggleSort("input_per_mtok")} active={sortKey === "input_per_mtok"} dir={sortDir} className="num">In $/Mtok</Th>
              <Th onClick={() => toggleSort("output_per_mtok")} active={sortKey === "output_per_mtok"} dir={sortDir} className="num">Out $/Mtok</Th>
              <Th onClick={() => toggleSort("arena_elo")} active={sortKey === "arena_elo"} dir={sortDir} className="num">Arena</Th>
              <Th>Status</Th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((m) => (
              <tr key={m.id} className="border-t border-paper-line dark:border-ink-line hover:bg-paper-panel/60 dark:hover:bg-ink-soft/60">
                <td className="px-3 py-2">
                  <Link href={modelHref(m.id)} className="hover:text-accent">
                    {m.name}
                  </Link>
                  {m.is_open_weight && <Badge tone="ok">open</Badge>}
                </td>
                <td className="px-3 py-2">
                  <span className="mr-1.5">{countryFlag(m.vendor_country)}</span>
                  {m.vendor_name}
                </td>
                <td className="px-3 py-2 num font-mono">{fmtTokens(m.context_window)}</td>
                <td className="px-3 py-2 text-xs">
                  {m.modalities?.map((x) => <Badge key={x} tone="muted">{x}</Badge>)}
                </td>
                <td className="px-3 py-2 num font-mono">{fmtPrice(m.input_per_mtok)}</td>
                <td className="px-3 py-2 num font-mono">{fmtPrice(m.output_per_mtok)}</td>
                <td className="px-3 py-2 num font-mono">{fmtElo(m.arena_elo)}</td>
                <td className="px-3 py-2">
                  {m.status === "active"     && <Badge tone="ok">active</Badge>}
                  {m.status === "preview"    && <Badge tone="warn">preview</Badge>}
                  {m.status === "deprecated" && <Badge tone="muted">deprecated</Badge>}
                  {m.status === "retired"    && <Badge tone="accent">retired</Badge>}
                </td>
              </tr>
            ))}
            {sorted.length === 0 && (
              <tr>
                <td colSpan={8} className="px-3 py-8 text-center text-ink-muted">No models match.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Th({ children, onClick, active, dir, className }: { children: React.ReactNode; onClick?: () => void; active?: boolean; dir?: "asc" | "desc"; className?: string }) {
  return (
    <th
      onClick={onClick}
      className={`px-3 py-2 ${onClick ? "cursor-pointer select-none" : ""} ${className ?? ""}`}
    >
      <span className={active ? "text-ink" : ""}>{children}</span>
      {active && <span className="ml-1 text-ink-muted">{dir === "asc" ? "↑" : "↓"}</span>}
    </th>
  );
}

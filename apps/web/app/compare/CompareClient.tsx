"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import Link from "next/link";
import type { ModelOverview } from "@/lib/types";
import { countryFlag, fmtDate, fmtElo, fmtPrice, fmtTokens, modelHref } from "@/lib/format";
import { Badge } from "@/components/Badge";

const MAX = 5;

type MetricRow = {
  label: string;
  render: (m: ModelOverview) => React.ReactNode;
};

const ELO_SUBS = [
  { key: "arena_elo_coding" as const, label: "↳ Coding" },
  { key: "arena_elo_vision" as const, label: "↳ Vision" },
];

const METRICS: MetricRow[] = [
  { label: "Vendor",         render: (m) => <>{countryFlag(m.vendor_country)} {m.vendor_name}</> },
  { label: "Input $/Mtok",   render: (m) => <span className="font-mono">{fmtPrice(m.input_per_mtok)}</span> },
  { label: "Output $/Mtok",  render: (m) => <span className="font-mono">{fmtPrice(m.output_per_mtok)}</span> },
  { label: "Cached $/Mtok",  render: (m) => <span className="font-mono">{fmtPrice(m.cached_input_per_mtok)}</span> },
  { label: "Context",        render: (m) => <span className="font-mono">{fmtTokens(m.context_window)}</span> },
  { label: "Arena ELO",      render: (m) => <span className="font-mono">{fmtElo(m.arena_elo)}</span> },
  { label: "Parameters",     render: (m) => <span className="font-mono">{m.parameters_b != null ? `${m.parameters_b}B` : "—"}</span> },
  { label: "Open weight",    render: (m) => m.is_open_weight ? <Badge tone="ok">yes</Badge> : <span className="text-ink-muted text-xs">no</span> },
  { label: "License",        render: (m) => m.license ? <span className="font-mono text-xs">{m.license}</span> : <span className="text-ink-muted text-xs">—</span> },
  { label: "Release date",   render: (m) => <span className="font-mono text-xs">{fmtDate(m.release_date)}</span> },
  { label: "Modalities",     render: (m) => <span className="text-xs">{(m.modalities ?? []).join(", ")}</span> },
  { label: "Status",         render: (m) => <Badge tone={m.status === "active" ? "ok" : m.status === "preview" ? "warn" : "muted"}>{m.status}</Badge> },
];

export function CompareClient({
  models,
  defaultModelId,
}: {
  models: ModelOverview[];
  defaultModelId: string | null;
}) {
  const [selected, setSelected]   = useState<string[]>(defaultModelId ? [defaultModelId] : []);
  const [searchQ, setSearchQ]     = useState("");
  const [open, setOpen]           = useState(false);
  const [eloExpanded, setEloExpanded] = useState(false);
  const inputRef                = useRef<HTMLInputElement>(null);
  const dropdownRef             = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (!dropdownRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const selectedModels = useMemo(
    () => selected.map((id) => models.find((m) => m.id === id)).filter(Boolean) as ModelOverview[],
    [selected, models],
  );

  const options = useMemo(() => {
    const q = searchQ.trim().toLowerCase();
    return models
      .filter((m) => !selected.includes(m.id))
      .filter((m) =>
        !q || m.name.toLowerCase().includes(q) || m.vendor_name.toLowerCase().includes(q),
      )
      .slice(0, 12);
  }, [models, selected, searchQ]);

  function add(id: string) {
    if (selected.length >= MAX) return;
    setSelected((prev) => [...prev, id]);
    setSearchQ("");
    setOpen(false);
    inputRef.current?.focus();
  }

  function remove(id: string) {
    setSelected((prev) => prev.filter((x) => x !== id));
  }

  return (
    <div className="space-y-6">
      {/* Selector */}
      <div className="flex flex-wrap gap-2 items-center">
        {selectedModels.map((m) => (
          <span
            key={m.id}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-accent/40 bg-accent/5 text-sm"
          >
            <span className="font-medium">{m.name}</span>
            <button
              onClick={() => remove(m.id)}
              className="text-ink-muted hover:text-ink leading-none"
              aria-label={`Remove ${m.name}`}
            >
              ×
            </button>
          </span>
        ))}

        {selected.length < MAX && (
          <div ref={dropdownRef} className="relative">
            <input
              ref={inputRef}
              value={searchQ}
              onChange={(e) => { setSearchQ(e.target.value); setOpen(true); }}
              onFocus={() => setOpen(true)}
              placeholder="+ Add model…"
              className="px-3 py-1.5 text-sm border border-paper-line rounded-full bg-white dark:bg-ink-soft dark:border-ink-line w-44 focus:outline-none focus:border-accent"
            />
            {open && options.length > 0 && (
              <div className="absolute top-full left-0 mt-1 z-30 w-72 bg-white dark:bg-ink-soft border border-paper-line dark:border-ink-line rounded-lg shadow-lg overflow-hidden">
                {options.map((m) => (
                  <button
                    key={m.id}
                    onMouseDown={() => add(m.id)}
                    className="w-full text-left px-4 py-2.5 text-sm hover:bg-paper-panel dark:hover:bg-ink/30 flex justify-between items-center gap-2"
                  >
                    <span className="font-medium truncate">{m.name}</span>
                    <span className="text-ink-muted text-xs shrink-0">{m.vendor_name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {selected.length > 0 && (
          <button
            onClick={() => setSelected([])}
            className="text-xs text-ink-muted hover:text-ink ml-auto"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Comparison table */}
      {selectedModels.length > 0 ? (
        <div className="overflow-x-auto border border-paper-line dark:border-ink-line rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-paper-panel dark:bg-ink-soft">
              <tr>
                <th className="px-4 py-3 text-left text-[11px] uppercase tracking-wider text-ink-muted w-36">
                  Metric
                </th>
                {selectedModels.map((m) => (
                  <th key={m.id} className="px-4 py-3 text-left min-w-[160px]">
                    <Link href={modelHref(m.id)} className="hover:text-accent font-semibold block truncate">
                      {m.name}
                    </Link>
                    <span className="text-xs font-normal text-ink-muted">
                      {countryFlag(m.vendor_country)} {m.vendor_name}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {METRICS.map((row) => (
                <>
                  <tr key={row.label} className="border-t border-paper-line dark:border-ink-line">
                    <td className="px-4 py-2.5 text-xs uppercase tracking-wider text-ink-muted font-mono whitespace-nowrap">
                      {row.label === "Arena ELO" ? (
                        <span className="inline-flex items-center gap-1.5">
                          Arena ELO
                          <button
                            onClick={() => setEloExpanded(e => !e)}
                            className="text-[10px] text-ink-muted hover:text-accent border border-current rounded px-0.5 leading-tight"
                            title={eloExpanded ? "Collapse" : "Expand sub-categories"}
                          >
                            {eloExpanded ? "◂" : "▸"}
                          </button>
                        </span>
                      ) : row.label}
                    </td>
                    {selectedModels.map((m) => (
                      <td key={m.id} className="px-4 py-2.5">
                        {row.render(m)}
                      </td>
                    ))}
                  </tr>
                  {row.label === "Arena ELO" && eloExpanded && ELO_SUBS.map((sub) => (
                    <tr key={sub.key} className="border-t border-paper-line/50 dark:border-ink-line/50 bg-paper-panel/40 dark:bg-ink-soft/20">
                      <td className="px-4 py-2 text-xs text-ink-muted font-mono whitespace-nowrap pl-6">
                        {sub.label}
                      </td>
                      {selectedModels.map((m) => (
                        <td key={m.id} className="px-4 py-2 font-mono text-sm text-ink-muted">
                          {fmtElo(m[sub.key])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="border border-paper-line dark:border-ink-line rounded-lg py-16 text-center text-ink-muted text-sm">
          Add models above to start comparing.
        </div>
      )}
    </div>
  );
}

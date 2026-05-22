/** Build a /models/[...id] URL — splits the id on '/' so each segment is encoded
 *  individually and the slash is preserved as a path separator. */
export function modelHref(id: string): string {
  return "/models/" + id.split("/").map(encodeURIComponent).join("/");
}

export function fmtPrice(v: number | null | undefined): string {
  if (v == null) return "—";
  if (v === 0) return "Free";
  if (v < 0.01) return `$${v.toFixed(4)}`;
  if (v < 1) return `$${v.toFixed(3)}`;
  return `$${v.toFixed(2)}`;
}

export function fmtTokens(v: number | null | undefined): string {
  if (v == null) return "—";
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(v % 1_000_000 ? 1 : 0)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}K`;
  return String(v);
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toISOString().slice(0, 10);
}

export function fmtTimeAgo(iso: string | null | undefined): string {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return iso;
  const diffSec = Math.floor((Date.now() - then) / 1000);
  if (diffSec < 60)     return `${diffSec}s ago`;
  if (diffSec < 3600)   return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400)  return `${Math.floor(diffSec / 3600)}h ago`;
  if (diffSec < 604800) return `${Math.floor(diffSec / 86400)}d ago`;
  return new Date(iso).toISOString().slice(0, 10);
}

export function fmtElo(v: number | null | undefined): string {
  if (v == null) return "—";
  return Math.round(v).toString();
}

export function fmtPct(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${v.toFixed(1)}%`;
}

const FLAGS: Record<string, string> = {
  US: "🇺🇸", CN: "🇨🇳", FR: "🇫🇷", CA: "🇨🇦", GB: "🇬🇧", DE: "🇩🇪",
};

export function countryFlag(code: string | null | undefined): string {
  if (!code) return "";
  return FLAGS[code] ?? code;
}

export function statusBadge(status: string): { label: string; cls: string } {
  switch (status) {
    case "active":     return { label: "active",     cls: "bg-emerald-100 text-emerald-900" };
    case "preview":    return { label: "preview",    cls: "bg-amber-100 text-amber-900" };
    case "deprecated": return { label: "deprecated", cls: "bg-stone-200 text-stone-700" };
    case "retired":    return { label: "retired",    cls: "bg-red-100 text-red-900" };
    default:           return { label: status,       cls: "bg-stone-200 text-stone-700" };
  }
}

import clsx from "clsx";

export function Badge({ children, tone = "default" }: { children: React.ReactNode; tone?: "default" | "muted" | "accent" | "ok" | "warn" }) {
  const cls = {
    default: "bg-stone-100 text-stone-800",
    muted:   "bg-stone-50 text-stone-500",
    accent:  "bg-accent-soft text-accent",
    ok:      "bg-emerald-50 text-emerald-800",
    warn:    "bg-amber-50 text-amber-800",
  }[tone];
  return (
    <span className={clsx("inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-mono uppercase tracking-wide", cls)}>
      {children}
    </span>
  );
}

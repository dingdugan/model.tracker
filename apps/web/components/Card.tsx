import { ReactNode } from "react";
import clsx from "clsx";

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={clsx(
        "rounded-lg border border-paper-line bg-white dark:border-ink-line dark:bg-ink-soft",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, right }: { title: string; subtitle?: string; right?: ReactNode }) {
  return (
    <div className="px-5 py-4 border-b border-paper-line dark:border-ink-line flex items-end justify-between gap-4">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-ink-muted">{title}</h2>
        {subtitle && <p className="text-base mt-0.5">{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}

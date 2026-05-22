import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import { getLatestSnapshot } from "@/lib/queries";
import { fmtTimeAgo } from "@/lib/format";

export const metadata: Metadata = {
  title: "model.tracker — Global AI model releases, pricing & benchmarks",
  description: "Daily-updated tracker of LLM releases, pricing, and benchmark performance across 14 major vendors.",
};

const NAV = [
  { href: "/",          label: "Overview" },
  { href: "/models",    label: "Models" },
  { href: "/pricing",   label: "Pricing" },
  { href: "/benchmarks", label: "Benchmarks" },
  { href: "/timeline",  label: "Timeline" },
  { href: "/changelog", label: "Changelog" },
];

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  let lastUpdated: string | null = null;
  try {
    const snap = await getLatestSnapshot();
    lastUpdated = snap?.snapshot_date ?? null;
  } catch {
    /* db unreachable at build — fine */
  }

  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col">
        <header className="border-b border-paper-line/80 dark:border-ink-line">
          <div className="mx-auto max-w-7xl px-6 py-4 flex items-center gap-8">
            <Link href="/" className="font-mono text-base font-semibold tracking-tight">
              model<span className="text-accent">.</span>tracker
            </Link>
            <nav className="flex items-center gap-5 text-sm">
              {NAV.map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  className="text-ink-muted hover:text-ink transition-colors"
                >
                  {n.label}
                </Link>
              ))}
            </nav>
            <div className="ml-auto text-xs font-mono text-ink-muted">
              {lastUpdated ? `Updated ${fmtTimeAgo(lastUpdated)}` : "—"}
            </div>
          </div>
        </header>

        <main className="flex-1">
          <div className="mx-auto max-w-7xl px-6 py-8">{children}</div>
        </main>

        <footer className="border-t border-paper-line/80 dark:border-ink-line mt-12">
          <div className="mx-auto max-w-7xl px-6 py-6 flex flex-wrap items-center justify-between gap-4 text-xs text-ink-muted">
            <div>
              Data sourced from vendor pricing pages, LMSYS Chatbot Arena, Artificial Analysis, and official benchmark reports.
            </div>
            <div className="flex items-center gap-4">
              <a href="https://github.com" target="_blank" rel="noreferrer" className="hover:text-ink">GitHub</a>
              <span>·</span>
              <span>Updates daily</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}

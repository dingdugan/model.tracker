import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import { getLatestSnapshot } from "@/lib/queries";

export const metadata: Metadata = {
  title: "model.tracker — Global AI model releases, pricing & benchmarks",
  description: "Daily-updated tracker of LLM releases, pricing, and benchmark performance across 14 major vendors.",
};

const NAV = [
  { href: "/compare",   label: "Compare" },
  { href: "/timeline",  label: "Timeline" },
  { href: "/changelog", label: "Changelog" },
];

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  let lastUpdated: string | null = null;
  try {
    const snap = await getLatestSnapshot();
    lastUpdated = snap?.snapshot_date ?? null;
  } catch { /* db unreachable at build */ }

  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col">
        <header className="border-b border-paper-line/80 dark:border-ink-line sticky top-0 z-40 bg-white/95 dark:bg-ink/95 backdrop-blur">
          <div className="mx-auto max-w-7xl px-6 py-3 flex items-center gap-8">
            <Link href="/" className="font-mono text-base font-semibold tracking-tight shrink-0">
              model<span className="text-accent">.</span>tracker
            </Link>
            <nav className="flex items-center gap-5 text-sm">
              {NAV.map((n) => (
                <Link key={n.href} href={n.href} className="text-ink-muted hover:text-ink transition-colors">
                  {n.label}
                </Link>
              ))}
            </nav>
            <div className="ml-auto text-xs font-mono text-ink-muted shrink-0">
              {lastUpdated ? `Updated ${lastUpdated}` : "—"}
            </div>
          </div>
        </header>

        <main className="flex-1">
          <div className="mx-auto max-w-7xl px-6 py-6">{children}</div>
        </main>

        <footer className="border-t border-paper-line/80 dark:border-ink-line mt-12">
          <div className="mx-auto max-w-7xl px-6 py-5 flex flex-wrap items-center justify-between gap-4 text-xs text-ink-muted">
            <span>Data: vendor pricing pages · LMSYS Chatbot Arena · Artificial Analysis · academic benchmarks. Updates daily.</span>
            <a href="https://github.com/dingdugan/model.tracker" target="_blank" rel="noreferrer" className="hover:text-ink">GitHub →</a>
          </div>
        </footer>
      </body>
    </html>
  );
}

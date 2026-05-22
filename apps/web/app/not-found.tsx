import Link from "next/link";

export default function NotFound() {
  return (
    <div className="text-center py-24">
      <p className="font-mono text-sm text-ink-muted">404</p>
      <h1 className="text-3xl font-semibold mt-2">Not found</h1>
      <p className="text-ink-muted mt-2">That page (or model) doesn't exist.</p>
      <Link href="/" className="inline-block mt-6 text-accent hover:underline">← Back to overview</Link>
    </div>
  );
}

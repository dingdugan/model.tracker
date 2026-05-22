"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PriceHistoryPoint } from "@/lib/types";

export function PriceChart({ data }: { data: PriceHistoryPoint[] }) {
  const series = data.map((p) => ({
    date: p.effective_date,
    input: p.input_per_mtok ?? null,
    output: p.output_per_mtok ?? null,
    cached: p.cached_input_per_mtok ?? null,
  }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={series} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} unit="$" />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="stepAfter" dataKey="input"  stroke="#0a0a0a" strokeWidth={1.5} dot={false} name="Input" />
          <Line type="stepAfter" dataKey="output" stroke="#dc2626" strokeWidth={1.5} dot={false} name="Output" />
          <Line type="stepAfter" dataKey="cached" stroke="#525252" strokeWidth={1.5} dot={false} strokeDasharray="4 2" name="Cached" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

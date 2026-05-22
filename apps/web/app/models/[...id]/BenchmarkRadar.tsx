"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";

export function BenchmarkRadar({ scores }: { scores: Array<{ name: string; value: number }> }) {
  // Recharts needs at least 3 points for a radar to look reasonable; pad otherwise.
  const data = scores.map((s) => ({ subject: s.name, value: s.value }));
  while (data.length < 3) data.push({ subject: "—", value: 0 });

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid stroke="#e7e5e4" />
          <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
          <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10 }} angle={90} />
          <Radar dataKey="value" stroke="#dc2626" fill="#dc2626" fillOpacity={0.25} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

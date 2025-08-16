import type { Summary } from "../lib/api";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, BarChart, Bar, CartesianGrid } from "recharts";

export default function Graphs({ summary }: { summary: Summary | null }) {
  const data = (summary?.trend ?? [1,2,3,4]).map((v, i) => ({ idx: i + 1, value: v }));
  return (
    <section>
      <h2>Graphs</h2>
      <div style={{ display:"grid", gap:16, gridTemplateColumns:"repeat(auto-fit,minmax(320px,1fr))" }}>
        <div style={{ border:"1px solid #eee", borderRadius:8, padding:12, height:260 }}>
          <div style={{ fontWeight:600, marginBottom:8 }}>Trend (Line)</div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="idx" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div style={{ border:"1px solid #eee", borderRadius:8, padding:12, height:260 }}>
          <div style={{ fontWeight:600, marginBottom:8 }}>Trend (Bar)</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="idx" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}

import { useEffect, useState } from "react";
import type { Summary } from "../lib/api";
import { getSummary } from "../lib/api";

export default function Dashboard({ token }: { token: string | null }) {
  const [summary, setSummary] = useState<Summary | null>(null);
  useEffect(() => {
    if (!token) { setSummary(null); return; }
    getSummary(token).then(setSummary).catch(() => setSummary(null));
  }, [token]);
  return (
    <section className="p-4">
      <h2 className="text-xl font-bold mb-2">Dashboard (Realtime)</h2>
      {!token && <p className="text-red-600">Login to view protected data.</p>}
      {summary ? (
        <div className="grid gap-3">
          <div className="rounded-lg border p-4"><div className="text-sm text-gray-500">Total</div><div className="text-2xl font-semibold">{summary.total}</div></div>
          <div className="rounded-lg border p-4">
            <div className="text-sm text-gray-500 mb-1">Trend</div>
            <div className="flex gap-1">
              {summary.trend.map((v,i)=>(
                <div key={i} title={String(v)} style={{height: 4+v*4, width:10}} className="bg-blue-500 rounded-sm" />
              ))}
            </div>
          </div>
        </div>
      ) : <p className="text-gray-500">—</p>}
    </section>
  );
}

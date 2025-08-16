import type { Summary } from "../lib/api";

export default function Analytics({ summary, authed }:{ summary: Summary|null; authed: boolean }) {
  return (
    <section className="p-4">
      <div className="mb-2 rounded bg-yellow-100 border border-yellow-300 text-yellow-800 px-3 py-2">
        Analytics are protected. {authed ? "You are signed in." : "Not signed in."}
      </div>
      <h2 className="text-xl font-bold mb-3">Analytics</h2>
      <div className="rounded-lg border p-4 mb-4">
        <div className="text-sm text-gray-500 mb-1">Trend</div>
        {summary ? (
          <div className="flex gap-1">
            {summary.trend.map((v,i)=>(
              <div key={i} title={String(v)} style={{height: 4+v*4, width:10}} className="bg-green-500 rounded-sm" />
            ))}
          </div>
        ) : <p className="text-gray-500">—</p>}
      </div>
      <div className="rounded-lg border p-4">
        <div className="text-sm text-gray-500 mb-2">Records (mock)</div>
        <div className="overflow-x-auto">
          <table className="min-w-[360px] text-sm">
            <thead><tr className="text-left text-gray-500"><th className="pr-4">ID</th><th className="pr-4">Name</th><th className="pr-4">Category</th><th>Value</th></tr></thead>
            <tbody>
              {(summary?.trend ?? []).map((v,i)=>(
                <tr key={i}><td className="pr-4">{i+1}</td><td className="pr-4">Item {i+1}</td><td className="pr-4">{v%2 ? "A":"B"}</td><td>{v}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

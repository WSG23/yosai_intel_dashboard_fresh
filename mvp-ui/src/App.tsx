import { useEffect, useState } from "react";
import Nav from "./components/Nav";
import { MetricCard } from "./components/MetricCard";
import { apiLogin, getSummary } from "./lib/api";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

type Summary = { total: number; trend: number[] };

export default function App() {
  const [token, setToken] = useState<string | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setError(null);
      setLoading(true);
      const data = await getSummary();
      setSummary(data);
    } catch (e: any) {
      setError(e?.message || "failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, []);

  async function doLogin() {
    try {
      const res = await apiLogin("demo", "x");
      setToken(res.token);
    } catch (e: any) {
      setError(e?.message || "login failed");
    }
  }

  function doLogout() { setToken(null); }

  const chartData = (summary?.trend || []).map((y, i) => ({ x: i + 1, y }));

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav onLogin={doLogin} onLogout={doLogout} authed={!!token} />
      <main className="max-w-5xl mx-auto p-4 space-y-6">
        <header className="mt-2">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-gray-600">MVP wired to /api</p>
        </header>

        {error && <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-red-700">{error}</div>}

        {loading ? (
          <div className="text-gray-600">Loading…</div>
        ) : (
          <>
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <MetricCard label="Total" value={summary?.total ?? "—"} />
              <MetricCard label="Authed" value={token ? "Yes" : "No"} />
              <MetricCard label="API Base" value={(import.meta as any).env?.VITE_API_BASE || "/api"} />
            </section>

            <section className="rounded-2xl border bg-white p-4 shadow-sm h-64">
              <div className="text-sm text-gray-500 mb-2">Trend</div>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <XAxis dataKey="x" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="y" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

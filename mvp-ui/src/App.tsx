import { useEffect, useMemo, useState } from "react";
import Nav from "./components/Nav";
import { getSummary, type Summary } from "./lib/api";
import Dashboard from "./pages/Dashboard";
import Analytics from "./pages/Analytics";
import Graphs from "./pages/Graphs";
import ExportPage from "./pages/Export";
import Upload from "./pages/Upload";
import Settings from "./pages/Settings";

type Tab = "dashboard"|"analytics"|"graphs"|"export"|"upload"|"settings";

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("token"));
  const [summary, setSummary] = useState<Summary | null>(null);

  const authed = !!token;
  useEffect(() => { if (token) localStorage.setItem("token", token); else localStorage.removeItem("token"); }, [token]);
  useEffect(() => { if (!token) { setSummary(null); return; } getSummary(token).then(setSummary).catch(()=>setSummary(null)); }, [token]);

  const Banner = useMemo(() => (
    !authed ? <div className="w-full bg-yellow-100 border-b border-yellow-300 text-yellow-800 px-3 py-2 text-sm">401 Unauthorized — Login to access protected data.</div> : null
  ), [authed]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav tab={tab} onSelect={setTab} onLogout={() => setToken(null)} />
      {Banner}
      <main className="max-w-5xl mx-auto">
        {tab==="dashboard" && <Dashboard token={token} />}
        {tab==="analytics" && <Analytics summary={summary} authed={authed} />}
        {tab==="graphs" && <Graphs summary={summary} />}
        {tab==="export" && <ExportPage token={token} />}
        {tab==="upload" && <Upload token={token} />}
        {tab==="settings" && <Settings token={token} onSetToken={setToken} />}
      </main>
    </div>
  );
}

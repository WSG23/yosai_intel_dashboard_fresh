import { useEffect, useState } from "react";
import Nav from "./components/Nav";
import LiveBanner from "./components/LiveBanner";
import Dashboard from "./pages/Dashboard";
import Analytics from "./pages/Analytics";
import Graphs from "./pages/Graphs";
import ExportPage from "./pages/Export";
import UploadPage from "./pages/Upload";
import Settings from "./pages/Settings";
import { apiLogin, getSummary, type Summary } from "./lib/api";

type Tab = "dashboard" | "analytics" | "graphs" | "export" | "upload" | "settings";
const getToken = () => localStorage.getItem("token");

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [token, setToken] = useState<string | null>(getToken());
  const [summary, setSummary] = useState<Summary | null>(null);
  const [err, setErr] = useState("");

  async function login() {
    setErr("");
    try {
      const { token } = await apiLogin("demo", "x");
      localStorage.setItem("token", token);
      setToken(token);
    } catch (e:any) {
      setErr(String(e));
    }
  }

  function logout() {
    localStorage.removeItem("token");
    setToken(null);
    setSummary(null);
  }

  useEffect(() => {
    const ctrl = new AbortController();
    (async () => {
      setErr("");
      setSummary(null);
      try {
        const s = await getSummary(token);
        setSummary(s);
      } catch (e:any) {
        setErr(String(e));
      }
    })();
    return () => ctrl.abort();
  }, [token]);

  return (
    <div style={{ padding: 20, fontFamily: "Inter, system-ui, sans-serif" }}>
      <header style={{ display:"flex", alignItems:"center", gap:12 }}>
        <h1 style={{ margin:0 }}>Yōsai Intel</h1>
        <button onClick={login} style={{ padding:"6px 10px", border:"1px solid #ddd", borderRadius:8 }}>Login</button>
      </header>
      <LiveBanner token={token} />
      <Nav tab={tab} setTab={setTab} onLogout={logout} />
      {err && <pre style={{ background:"#fee", padding:8, border:"1px solid #fbb" }}>{err}</pre>}
      <main style={{ marginTop:12 }}>
        {tab === "dashboard" && <Dashboard token={token} summary={summary} />}
        {tab === "analytics" && <Analytics summary={summary} />}
        {tab === "graphs" && <Graphs summary={summary} />}
        {tab === "export" && <ExportPage token={token} />}
        {tab === "upload" && <UploadPage token={token} />}
        {tab === "settings" && <Settings token={token} clear={logout} />}
      </main>
    </div>
  );
}

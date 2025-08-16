import { useEffect, useState } from "react";
import { API_BASE, type Summary } from "../lib/api";

export default function Dashboard({ token, summary }: { token: string | null; summary: Summary | null }) {
  const [ticks, setTicks] = useState(0);
  const [last, setLast] = useState<string>("—");

  useEffect(() => {
    if (!token) return;
    const es = new EventSource(`${API_BASE}/events?token=${encodeURIComponent(token)}`);
    es.onmessage = (ev) => { setTicks(t => t + 1); setLast(ev.data || ""); };
    es.onerror = () => { try { es.close(); } catch { /* noop */ } };
    return () => { try { es.close(); } catch { /* noop */ } };
  }, [token]);

  return (
    <section>
      <h2>Dashboard</h2>
      {!token && <p style={{color:"#a00"}}>Login to start the live feed.</p>}
      <div style={{ display:"grid", gap:12, gridTemplateColumns:"repeat(auto-fit,minmax(220px,1fr))", marginBottom:12 }}>
        <div style={{ border:"1px solid #eee", borderRadius:8, padding:12 }}>
          <div style={{ fontSize:12, color:"#666" }}>Total</div>
          <div style={{ fontSize:28, fontWeight:700 }}>{summary ? summary.total : "—"}</div>
        </div>
        <div style={{ border:"1px solid #eee", borderRadius:8, padding:12 }}>
          <div style={{ fontSize:12, color:"#666" }}>Live ticks</div>
          <div style={{ fontSize:28, fontWeight:700 }}>{ticks}</div>
        </div>
      </div>
      <div style={{ border:"1px solid #eef", background:"#f8fbff", padding:12, borderRadius:8, marginBottom:12 }}>
        <div style={{ fontWeight:600, marginBottom:6 }}>Last event</div>
        <pre style={{ margin:0, whiteSpace:"pre-wrap", wordBreak:"break-word" }}>{last}</pre>
      </div>
      <div>
        <div style={{ fontWeight:600, marginBottom:6 }}>Trend</div>
        <div>{summary ? summary.trend.join(", ") : "—"}</div>
      </div>
    </section>
  );
}

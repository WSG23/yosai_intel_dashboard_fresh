import { API_BASE } from "../lib/api";
export default function LiveBanner({ token }: { token: string | null }) {
  return (
    <div style={{ background:"#eef6ff", border:"1px solid #cfe3ff", padding:8, borderRadius:8, margin:"8px 0", display:"flex", gap:12, alignItems:"center" }}>
      <span style={{ fontWeight:600 }}>Live</span>
      <span>Authed: {token ? "Yes" : "No"}</span>
      <span>API: {API_BASE}</span>
    </div>
  );
}

type Tab = "dashboard" | "analytics" | "graphs" | "export" | "upload" | "settings";
export default function Nav({ tab, setTab, onLogout }: { tab: Tab; setTab: (t: Tab)=>void; onLogout: ()=>void }) {
  const Item = ({ id, label }: { id: Tab; label: string }) => (
    <button
      onClick={()=>setTab(id)}
      style={{
        padding: "8px 12px",
        border: "1px solid #ddd",
        borderRadius: 8,
        background: tab === id ? "#111" : "#fff",
        color: tab === id ? "#fff" : "#111",
        cursor: "pointer"
      }}
    >{label}</button>
  );
  return (
    <nav style={{ display:"flex", gap:8, padding:"8px 0", flexWrap:"wrap" }}>
      <Item id="dashboard" label="Dashboard" />
      <Item id="analytics" label="Analytics" />
      <Item id="graphs" label="Graphs" />
      <Item id="export" label="Export" />
      <Item id="upload" label="Upload" />
      <Item id="settings" label="Settings" />
      <span style={{ flex:1 }} />
      <button onClick={onLogout} style={{ padding:"8px 12px", border:"1px solid #f33", borderRadius:8, background:"#fff", color:"#f33", cursor:"pointer" }}>Logout</button>
    </nav>
  );
}

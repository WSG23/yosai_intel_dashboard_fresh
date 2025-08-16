import { downloadCSV } from "../lib/api";
export default function ExportPage({ token }: { token: string | null }) {
  async function onClick() { await downloadCSV(token); }
  return (
    <section>
      <h2>Export</h2>
      <button onClick={onClick} disabled={!token} style={{ padding:"8px 12px", border:"1px solid #ddd", borderRadius:8 }}>Download CSV</button>
      {!token && <p style={{color:"#a00"}}>Login first to enable export.</p>}
    </section>
  );
}

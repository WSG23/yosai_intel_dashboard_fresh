import { useState } from "react";
import { uploadFile } from "../lib/api";
export default function UploadPage({ token }: { token: string | null }) {
  const [out, setOut] = useState<any>(null);
  const [err, setErr] = useState<string>("");

  async function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    setErr(""); setOut(null);
    const f = e.target.files?.[0];
    if (!f) return;
    try {
      const j = await uploadFile(f, token);
      setOut(j);
    } catch (e:any) {
      setErr(String(e));
    }
  }

  return (
    <section>
      <h2>Upload</h2>
      <input type="file" accept=".csv" onChange={onChange} disabled={!token} />
      {!token && <p style={{color:"#a00"}}>Login first to enable upload.</p>}
      {err && <pre style={{background:"#fee", border:"1px solid #fbb", padding:8}}>{err}</pre>}
      {out && <pre style={{background:"#eef", border:"1px solid #bbf", padding:8, maxHeight:240, overflow:"auto"}}>{JSON.stringify(out, null, 2)}</pre>}
    </section>
  );
}

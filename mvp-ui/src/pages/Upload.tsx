import { useState } from 'react';
export default function Upload({ token }: { token: string | null }) {
  const [msg,setMsg]=useState('Choose a CSV to upload');
  const [columns,setColumns]=useState<string[]>([]);
  const [rows,setRows]=useState<any[]>([]);
  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if(!file || !token) return;
    const fd = new FormData(); fd.append('file', file);
    const res = await fetch('/api/upload',{method:'POST',headers:{Authorization:`Bearer ${token}`},body:fd});
    if(!res.ok){ setMsg(`Upload failed: ${res.status}`); return; }
    const data = await res.json();
    setMsg(`Uploaded ${data.filename} (${(data.rows?.length??0)} rows)`);
    setColumns(data.columns??[]); setRows(data.rows??[]);
  }
  return (
    <div className="space-y-3">
      <input type="file" accept=".csv,text/csv" onChange={onFile} disabled={!token}/>
      <p>{msg}</p>
      {columns.length>0 && (
        <div>
          <div className="text-sm opacity-70">Columns: {columns.join(', ')}</div>
          <div className="overflow-auto border rounded">
            <table className="min-w-full text-sm">
              <thead><tr>{columns.map(c=><th key={c} className="p-2 text-left border-b">{c}</th>)}</tr></thead>
              <tbody>
                {rows.slice(0,20).map((r,i)=><tr key={i}>{columns.map(c=><td key={c} className="p-2 border-b">{String(r[c]??'')}</td>)}</tr>)}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

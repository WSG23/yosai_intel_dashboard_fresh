export default function Export({ token }: { token: string | null }) {
  async function dl() {
    if (!token) return;
    const res = await fetch('/api/export', {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('export failed');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement('a'), { href: url, download: 'export.csv' });
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }
  return <button onClick={dl} disabled={!token}>Download CSV</button>;
}

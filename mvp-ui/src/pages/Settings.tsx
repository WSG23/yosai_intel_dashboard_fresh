export default function Settings({ token, clear }: { token: string | null; clear: ()=>void }) {
  return (
    <section>
      <h2>Settings</h2>
      <p>Token: {token ?? "—"}</p>
      <button onClick={clear} style={{ padding:"8px 12px", border:"1px solid #ddd", borderRadius:8 }}>Clear token</button>
    </section>
  );
}

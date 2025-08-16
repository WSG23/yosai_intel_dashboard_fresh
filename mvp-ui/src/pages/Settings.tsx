import { login } from "../lib/api";
export default function Settings({ token, onSetToken }:{ token: string|null; onSetToken:(t:string|null)=>void }) {
  async function handleLogin() {
    const r = await login("demo","x");
    onSetToken(r.token);
  }
  return (
    <section className="p-4">
      <h2 className="text-xl font-bold mb-2">Settings</h2>
      <div className="mb-2"><span className="text-gray-500">API Base:</span> /api</div>
      <div className="mb-2"><span className="text-gray-500">Token:</span> {token ?? "—"}</div>
      <div className="flex gap-2">
        {!token ? (
          <button onClick={handleLogin} className="px-3 py-2 rounded bg-green-600 text-white">Login (demo)</button>
        ) : (
          <button onClick={()=>onSetToken(null)} className="px-3 py-2 rounded bg-red-600 text-white">Clear token</button>
        )}
      </div>
    </section>
  );
}

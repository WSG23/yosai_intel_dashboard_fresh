import { apiBase } from '../lib/api';
type Props = { token: string | null; onLogout: () => void };
export default function Settings({ token, onLogout }: Props) {
  return (
    <section style={{ display: 'grid', gap: 12 }}>
      <h2 style={{ fontSize: 20, fontWeight: 700 }}>Settings</h2>
      <div>API Base: <code>{apiBase()}</code></div>
      <div>Auth: {token ? <><b>Yes</b> <button onClick={onLogout}>Logout</button></> : 'No'}</div>
    </section>
  );
}

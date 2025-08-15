import { useEffect, useState } from 'react';
import Nav from './components/Nav';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import { apiLogin, getSummary, type Summary } from './lib/api';
export default function App() {
  const [page, setPage] = useState<'dashboard'|'analytics'|'settings'>('dashboard');
  const [token, setToken] = useState<string | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => { getSummary().then(setSummary).catch(() => setSummary(null)); }, []);
  async function login() {
    setLoading(true);
    try { const res = await apiLogin('demo', 'x'); setToken(res.token); }
    finally { setLoading(false); }
  }
  function logout(){ setToken(null); }
  return (
    <div style={{ maxWidth: 1200, margin: '24px auto', padding: 16, display: 'grid', gap: 16 }}>
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h1 style={{ fontSize: 22, fontWeight: 800 }}>Yōsai Intel</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={login} disabled={loading} className="px-3 py-2 bg-black text-white rounded">
            {token ? 'Re-Login' : 'Login'}
          </button>
        </div>
      </header>
      <Nav page={page} onNavigate={(p) => setPage(p as any)} />
      <main>
        {page === 'dashboard' && <Dashboard summary={summary} token={token} />}
        {page === 'analytics' && <Analytics summary={summary} />}
        {page === 'settings' && <Settings token={token} onLogout={logout} />}
      </main>
    </div>
  );
}

import React from 'react';

export function NavCards(props: { total?: number; trend?: number[]; authed: boolean; apiBase: string; onLogin: () => void; onLogout: () => void; }) {
  const { total, trend, authed, apiBase, onLogin, onLogout } = props;
  return (
    <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
      <div style={{ padding: 16, border: '1px solid #eee', borderRadius: 12 }}>
        <div style={{ fontSize: 12, color: '#666' }}>Total</div>
        <div style={{ fontSize: 28, fontWeight: 700 }}>{total ?? '—'}</div>
      </div>
      <div style={{ padding: 16, border: '1px solid #eee', borderRadius: 12 }}>
        <div style={{ fontSize: 12, color: '#666' }}>Authed</div>
        <div style={{ fontSize: 28, fontWeight: 700 }}>{authed ? 'Yes' : 'No'}</div>
        <div style={{ marginTop: 8 }}>
          {authed ? <button onClick={onLogout}>Logout</button> : <button onClick={onLogin}>Login</button>}
        </div>
      </div>
      <div style={{ padding: 16, border: '1px solid #eee', borderRadius: 12 }}>
        <div style={{ fontSize: 12, color: '#666' }}>API Base</div>
        <div style={{ fontSize: 14 }}>{apiBase}</div>
      </div>
      <div style={{ padding: 16, border: '1px solid #eee', borderRadius: 12 }}>
        <div style={{ fontSize: 12, color: '#666' }}>Trend</div>
        <div style={{ fontSize: 14 }}>{trend?.join(' · ') ?? '—'}</div>
      </div>
    </div>
  );
}
export default NavCards;

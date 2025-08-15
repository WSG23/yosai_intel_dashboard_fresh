import type { Summary } from '../lib/api';
type Props = { summary: Summary | null; token: string | null };
export default function Dashboard({ summary, token }: Props) {
  return (
    <section style={{ display: 'grid', gap: 12 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0,1fr))', gap: 12 }}>
        <div style={{ padding: 16, border: '1px solid #ddd', borderRadius: 12 }}>
          <div style={{ fontSize: 12, color: '#666' }}>Total</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{summary ? summary.total : '—'}</div>
        </div>
        <div style={{ padding: 16, border: '1px solid #ddd', borderRadius: 12 }}>
          <div style={{ fontSize: 12, color: '#666' }}>Authed</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{token ? 'Yes' : 'No'}</div>
        </div>
        <div style={{ padding: 16, border: '1px solid #ddd', borderRadius: 12 }}>
          <div style={{ fontSize: 12, color: '#666' }}>Trend</div>
          <div style={{ fontSize: 18 }}>{summary ? summary.trend.join(', ') : '—'}</div>
        </div>
        <div style={{ padding: 16, border: '1px solid #ddd', borderRadius: 12 }}>
          <div style={{ fontSize: 12, color: '#666' }}>Status</div>
          <div style={{ fontSize: 18 }}>MVP wired to /api</div>
        </div>
      </div>
    </section>
  );
}

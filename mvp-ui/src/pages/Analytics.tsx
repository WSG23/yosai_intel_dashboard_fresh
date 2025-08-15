import type { Summary } from '../lib/api';
type Props = { summary: Summary | null };
export default function Analytics({ summary }: Props) {
  if (!summary) return <p>Loading…</p>;
  return (
    <section style={{ display: 'grid', gap: 12 }}>
      <h2 style={{ fontSize: 20, fontWeight: 700 }}>Analytics</h2>
      <ul style={{ listStyle: 'disc', paddingLeft: 18 }}>
        <li>Total: {summary.total}</li>
        <li>Trend: {summary.trend.join(', ')}</li>
      </ul>
    </section>
  );
}

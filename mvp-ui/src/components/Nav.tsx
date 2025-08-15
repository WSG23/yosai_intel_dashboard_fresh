type Props = { page: string; onNavigate: (p: string) => void };
export default function Nav({ page, onNavigate }: Props) {
  const Item = ({ id, label }: { id: string; label: string }) => (
    <button onClick={() => onNavigate(id)}
      className={`px-3 py-2 rounded ${page === id ? 'bg-black text-white' : 'bg-gray-200'}`}
      aria-current={page === id ? 'page' : undefined}>{label}</button>
  );
  return (
    <nav style={{ display: 'flex', gap: 8 }}>
      <Item id="dashboard" label="Dashboard" />
      <Item id="analytics" label="Analytics" />
      <Item id="settings" label="Settings" />
    </nav>
  );
}

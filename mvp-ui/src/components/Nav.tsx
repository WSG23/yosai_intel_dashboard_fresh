type Props = { onLogin: () => void; onLogout: () => void; authed: boolean };
export default function Nav({ onLogin, onLogout, authed }: Props) {
  return (
    <nav className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="font-semibold">Yōsai Intel</div>
        <div className="space-x-2">
          {authed ? (
            <button className="px-3 py-1 rounded-xl border shadow-sm" onClick={onLogout}>Logout</button>
          ) : (
            <button className="px-3 py-1 rounded-xl border shadow-sm" onClick={onLogin}>Login</button>
          )}
        </div>
      </div>
    </nav>
  );
}

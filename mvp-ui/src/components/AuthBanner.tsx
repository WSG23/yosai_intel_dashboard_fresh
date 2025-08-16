import { useEffect, useState } from "react";
import Banner from "./Banner";

export default function AuthBanner({ token, page }: { token: string | null; page: string }) {
  const [recentLogout, setRecentLogout] = useState(false);

  useEffect(() => {
    const onLogout = () => setRecentLogout(true);
    window.addEventListener("auth:logout", onLogout as EventListener);
    return () => window.removeEventListener("auth:logout", onLogout as EventListener);
  }, []);

  if (token) return null;
  const msg = recentLogout
    ? `Session ended. Please sign in again to view ${page}.`
    : `Login to view ${page}.`;
  return <Banner kind="warn" message={msg} />;
}

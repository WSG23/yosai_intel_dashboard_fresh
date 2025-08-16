export default function Banner({ kind = "info", message }: { kind?: "info"|"warn"|"error"|"success"; message: string }) {
  const base = "w-full px-3 py-2 rounded mb-2";
  const cls = kind === "error" ? base + " bg-red-100 text-red-800"
    : kind === "warn" ? base + " bg-yellow-100 text-yellow-800"
    : kind === "success" ? base + " bg-green-100 text-green-800"
    : base + " bg-blue-100 text-blue-800";
  return <div className={cls}>{message}</div>;
}

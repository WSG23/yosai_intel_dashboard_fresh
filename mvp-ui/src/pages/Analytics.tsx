import type { Summary } from "../lib/api";
export default function Analytics({ summary }: { summary: Summary | null }) {
  const records = [
    { id: 1, name: "Alpha", category: "A", value: 10 },
    { id: 2, name: "Beta", category: "B", value: 20 },
    { id: 3, name: "Gamma", category: "A", value: 15 }
  ];
  return (
    <section>
      <h2>Analytics</h2>
      <p>Summary: {summary ? `${summary.total} [${summary.trend.join(", ")}]` : "—"}</p>
      <div style={{ overflowX:"auto" }}>
        <table style={{ width:"100%", borderCollapse:"collapse" }}>
          <thead>
            <tr><th style={{textAlign:"left"}}>ID</th><th style={{textAlign:"left"}}>Name</th><th style={{textAlign:"left"}}>Category</th><th style={{textAlign:"left"}}>Value</th></tr>
          </thead>
          <tbody>
            {records.map(r=>(
              <tr key={r.id}>
                <td>{r.id}</td><td>{r.name}</td><td>{r.category}</td><td>{r.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

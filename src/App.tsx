import { useEffect, useState } from 'react'
type Summary = { total: number; trend: number[] }
export default function App() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [token, setToken] = useState<string>('')
  useEffect(() => { fetch('/api/analytics/summary').then(r => r.json()).then(setSummary) }, [])
  const login = async () => {
    const r = await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:'demo',password:'demo'})})
    const data = await r.json(); setToken(data.token)
  }
  return (
    <div style={{fontFamily:'system-ui',padding:24}}>
      <h1>Dashboard MVP</h1>
      <button onClick={login}>Login</button>
      {token && <p>Token: {token}</p>}
      {summary ? (<><p>Total: {summary.total}</p><p>Trend: {summary.trend.join(', ')}</p></>) : (<p>Loading…</p>)}
    </div>
  )
}

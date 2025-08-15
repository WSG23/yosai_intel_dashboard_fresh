import { useEffect, useState } from 'react'
type Summary = { total: number; trend: number[] }

export default function App() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [token, setToken] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch('/api/analytics/summary')
        if (!r.ok) throw new Error(`GET /api/analytics/summary -> ${r.status}`)
        setSummary(await r.json())
      } catch (e: any) { setError(e?.message ?? 'Failed to load summary') }
    }
    load()
  }, [])

  const login = async () => {
    try {
      const r = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ username:'demo', password:'demo' })
      })
      if (!r.ok) throw new Error(`POST /api/login -> ${r.status}`)
      const data = await r.json()
      setToken(data.token)
    } catch (e:any) { setError(e?.message ?? 'Login failed') }
  }

  return (
    <div style={{padding:24,fontFamily:'system-ui'}}>
      <h1>Dashboard MVP</h1>
      <button onClick={login} style={{padding:'8px 12px'}}>Login</button>
      {token && <p>Token: {token}</p>}
      {error && <p style={{color:'#b91c1c'}}>Error: {error}</p>}
      {summary ? (<><p>Total: {summary.total}</p><p>Trend: {summary.trend.join(', ')}</p></>) : (<p>Loading…</p>)}
    </div>
  )
}

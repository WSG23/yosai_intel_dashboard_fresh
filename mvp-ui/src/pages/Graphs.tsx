import { useEffect, useState } from 'react';
import type { Summary } from '../lib/api';
import { ResponsiveContainer, AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
export default function Graphs({ token }: { token: string | null }) {
  const [summary,setSummary]=useState<Summary|null>(null);
  useEffect(()=>{ let stop=false;
    async function load(){
      if(!token){ setSummary(null); return; }
      const res=await fetch('/api/analytics/summary',{headers:{Authorization:`Bearer ${token}`}});
      if(res.ok){ const d=await res.json(); if(!stop) setSummary(d); }
    }
    load(); return ()=>{ stop=true; };
  },[token]);
  const data=(summary?.trend??[]).map((y,i)=>({i,y}));
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="h-64 border rounded p-2">
        <div className="mb-2 font-medium">Trend (Area)</div>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}><XAxis dataKey="i"/><YAxis/><Tooltip/><Area dataKey="y" type="monotone"/></AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="h-64 border rounded p-2">
        <div className="mb-2 font-medium">Trend (Bar)</div>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}><XAxis dataKey="i"/><YAxis/><Tooltip/><Bar dataKey="y"/></BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

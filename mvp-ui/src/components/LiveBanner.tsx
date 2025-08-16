import { useEffect, useState } from 'react';
import { openEvents } from '../lib/events';
export default function LiveBanner({ token }: { token: string | null }) {
  const [tick,setTick]=useState<number|null>(null);
  useEffect(()=>{ if(!token) return;
    const close=openEvents(token,(d:any)=>{ if(d?.type==='tick') setTick(d.n); });
    return close;
  },[token]);
  return <div className="p-2 rounded bg-yellow-100 text-yellow-900 text-sm">{token? (tick?`Realtime tick: ${tick}`:'Listening…') : 'Login to start realtime feed'}</div>;
}

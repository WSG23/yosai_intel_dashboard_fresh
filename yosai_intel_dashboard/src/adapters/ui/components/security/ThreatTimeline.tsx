import React, { useMemo, useState } from "react";
import {
  Brush,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { useSelectionStore } from "../../state/store";

interface ThreatEvent {
  id: string;
  timestamp: string | number;
  track: string;
  severity?: number;
  correlatedWith?: string[];
}

interface ThreatTimelineProps {
  events: ThreatEvent[];
}

const yearMs = 365 * 24 * 60 * 60 * 1000;
const dayMs = 24 * 60 * 60 * 1000;
const hourMs = 60 * 60 * 1000;
const minuteMs = 60 * 1000;

const ThreatTimeline: React.FC<ThreatTimelineProps> = ({ events }) => {
  const { setSelectedThreats, setSelectedRange } = useSelectionStore();
  const [viewRange, setViewRange] = useState<[number, number] | null>(null);

  const tracks = useMemo(
    () => Array.from(new Set(events.map((e) => e.track))),
    [events],
  );

  const clusters = useMemo(() => {
    if (events.length === 0)
      return [] as { track: string; timestamp: number; count: number }[];
    const start =
      viewRange?.[0] ?? Math.min(...events.map((e) => +new Date(e.timestamp)));
    const end =
      viewRange?.[1] ?? Math.max(...events.map((e) => +new Date(e.timestamp)));
    const span = end - start;
    let bucket = 1000; // second
    if (span > yearMs) bucket = dayMs * 30;
    else if (span > dayMs * 30) bucket = dayMs;
    else if (span > dayMs) bucket = hourMs;
    else if (span > hourMs) bucket = minuteMs;

    const map = new Map<
      string,
      { track: string; timestamp: number; count: number }
    >();
    for (const ev of events) {
      const time = Math.floor(+new Date(ev.timestamp) / bucket) * bucket;
      const key = `${ev.track}-${time}`;
      const existing = map.get(key);
      if (existing) existing.count += 1;
      else map.set(key, { track: ev.track, timestamp: time, count: 1 });
    }
    return Array.from(map.values());
  }, [events, viewRange]);

  const { scatterSeries, lineSegments, predictionPoints, brushData } =
    useMemo(() => {
      const trackIndex: Record<string, number> = {};
      tracks.forEach((t, i) => {
        trackIndex[t] = i;
      });

      const scatterData: Record<string, any[]> = {};
      tracks.forEach((t) => (scatterData[t] = []));
      clusters.forEach((c) => {
        scatterData[c.track].push({
          x: c.timestamp,
          y: trackIndex[c.track],
          z: c.count,
        });
      });

      const scatters = tracks.map((t) => ({ name: t, data: scatterData[t] }));

      const eventMap = new Map(events.map((e) => [e.id, e]));
      const lines: { from: [number, number]; to: [number, number] }[] = [];
      events.forEach((ev) => {
        ev.correlatedWith?.forEach((id) => {
          const target = eventMap.get(id);
          if (target) {
            lines.push({
              from: [+new Date(ev.timestamp), trackIndex[ev.track]],
              to: [+new Date(target.timestamp), trackIndex[target.track]],
            });
          }
        });
      });

      const predictions: { x: number; y: number }[] = [];
      tracks.forEach((t) => {
        const evs = events
          .filter((e) => e.track === t)
          .sort((a, b) => +new Date(a.timestamp) - +new Date(b.timestamp));
        if (evs.length >= 2) {
          const last = +new Date(evs[evs.length - 1].timestamp);
          const prev = +new Date(evs[evs.length - 2].timestamp);
          const next = last + (last - prev);
          predictions.push({ x: next, y: trackIndex[t] });
        }
      });

      const brush = events
        .map((e) => ({ x: +new Date(e.timestamp), id: e.id }))
        .sort((a, b) => a.x - b.x);

      return {
        scatterSeries: scatters,
        lineSegments: lines,
        predictionPoints: predictions,
        brushData: brush,
      };
    }, [tracks, clusters, events]);

  const handleBrushChange = (range: {
    startIndex?: number;
    endIndex?: number;
  }) => {
    if (
      range.startIndex === undefined ||
      range.endIndex === undefined ||
      brushData.length === 0
    )
      return;
    const start = brushData[Math.min(range.startIndex, range.endIndex)].x;
    const end = brushData[Math.max(range.startIndex, range.endIndex)].x;
    setViewRange([start, end]);
    setSelectedRange([start, end]);
    const ids = events
      .filter((e) => {
        const t = +new Date(e.timestamp);
        return t >= start && t <= end;
      })
      .map((e) => e.id);
    setSelectedThreats(ids);
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <CartesianGrid />
        <XAxis
          type="number"
          dataKey="x"
          domain={["auto", "auto"]}
          tickFormatter={(v) => new Date(v).toLocaleString()}
        />
        <YAxis
          type="number"
          dataKey="y"
          ticks={tracks.map((_, i) => i)}
          tickFormatter={(v) => tracks[v]}
        />
        <ZAxis type="number" dataKey="z" range={[6, 30]} />
        <Tooltip
          cursor={{ strokeDasharray: "3 3" }}
          formatter={(value: any, _name, props) => {
            const time = new Date(props.payload.x);
            const count = props.payload.z || 1;
            return [`Count: ${count}`, time.toLocaleString()];
          }}
        />
        {scatterSeries.map((s) => (
          <Scatter key={s.name} name={s.name} data={s.data} />
        ))}
        {predictionPoints.map((p, i) => (
          <Scatter
            key={`pred-${i}`}
            data={[{ x: p.x, y: p.y, z: 1 }]}
            shape="diamond"
            fill="#aaa"
          />
        ))}
        {lineSegments.map((seg, i) => (
          <Line
            key={`line-${i}`}
            data={[
              { x: seg.from[0], y: seg.from[1] },
              { x: seg.to[0], y: seg.to[1] },
            ]}
            type="linear"
            dataKey="y"
            stroke="#888"
            strokeWidth={1}
            dot={false}
            isAnimationActive={false}
          />
        ))}
        <Brush
          dataKey="x"
          height={20}
          travellerWidth={10}
          data={brushData}
          onChange={handleBrushChange}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
};

export default ThreatTimeline;

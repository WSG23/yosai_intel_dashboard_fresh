import React, { useMemo, useRef, useState } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import {
  TimelineComponent,
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  BrushComponent,
} from 'echarts/components';
import { ScatterChart, LinesChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import { useSelectionStore } from '../../state/store';

echarts.use([
  TimelineComponent,
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  BrushComponent,
  ScatterChart,
  LinesChart,
  CanvasRenderer,
]);

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

const ReactECharts = ReactEChartsCore;

const ThreatTimeline: React.FC<ThreatTimelineProps> = ({ events }) => {
  const chartRef = useRef<ReactEChartsCore>(null);
  const { setSelectedThreats, setSelectedRange } = useSelectionStore();
  const [viewRange, setViewRange] = useState<[number, number] | null>(null);

  const tracks = useMemo(
    () => Array.from(new Set(events.map((e) => e.track))),
    [events],
  );

  const clusters = useMemo(() => {
    if (events.length === 0) return [] as { track: string; timestamp: number; count: number }[];
    const start = viewRange?.[0] ?? Math.min(...events.map((e) => +new Date(e.timestamp)));
    const end = viewRange?.[1] ?? Math.max(...events.map((e) => +new Date(e.timestamp)));
    const span = end - start;
    let bucket = 1000; // second
    if (span > yearMs) bucket = dayMs * 30;
    else if (span > dayMs * 30) bucket = dayMs;
    else if (span > dayMs) bucket = hourMs;
    else if (span > hourMs) bucket = minuteMs;

    const map = new Map<string, { track: string; timestamp: number; count: number }>();
    for (const ev of events) {
      const time = Math.floor(+new Date(ev.timestamp) / bucket) * bucket;
      const key = `${ev.track}-${time}`;
      const existing = map.get(key);
      if (existing) existing.count += 1;
      else map.set(key, { track: ev.track, timestamp: time, count: 1 });
    }
    return Array.from(map.values());
  }, [events, viewRange]);

  const series = useMemo(() => {
    const trackIndex: Record<string, number> = {};
    tracks.forEach((t, i) => {
      trackIndex[t] = i;
    });

    const scatterData: Record<string, any[]> = {};
    tracks.forEach((t) => (scatterData[t] = []));
    clusters.forEach((c) => {
      scatterData[c.track].push([c.timestamp, trackIndex[c.track], c.count]);
    });

    const scatterSeries = tracks.map((t) => ({
      name: t,
      type: 'scatter',
      data: scatterData[t],
      symbolSize: (val: number[]) => 8 + Math.log2(val[2] || 1) * 5,
      emphasis: { focus: 'series' },
    }));

    const eventMap = new Map(events.map((e) => [e.id, e]));
    const linesData: any[] = [];
    events.forEach((ev) => {
      ev.correlatedWith?.forEach((id) => {
        const target = eventMap.get(id);
        if (target) {
          linesData.push({
            coords: [
              [+new Date(ev.timestamp), trackIndex[ev.track]],
              [+new Date(target.timestamp), trackIndex[target.track]],
            ],
          });
        }
      });
    });

    const linesSeries = {
      name: 'correlation',
      type: 'lines',
      coordinateSystem: 'cartesian2d',
      data: linesData,
      lineStyle: { color: '#888', width: 1, curveness: 0.2 },
      silent: true,
    };

    const predictionSeries: any[] = [];
    tracks.forEach((t) => {
      const evs = events
        .filter((e) => e.track === t)
        .sort((a, b) => +new Date(a.timestamp) - +new Date(b.timestamp));
      if (evs.length >= 2) {
        const last = +new Date(evs[evs.length - 1].timestamp);
        const prev = +new Date(evs[evs.length - 2].timestamp);
        const next = last + (last - prev);
        predictionSeries.push({
          name: `${t}-prediction`,
          type: 'scatter',
          data: [[next, trackIndex[t], 1]],
          symbol: 'diamond',
          itemStyle: { color: '#aaa' },
          symbolSize: 8,
        });
      }
    });

    return [...scatterSeries, linesSeries, ...predictionSeries];
  }, [tracks, clusters, events]);

  const option = useMemo(
    () => ({
      timeline: {
        axisType: 'time',
        show: false,
      },
      tooltip: {
        trigger: 'item',
        formatter: (p: any) => {
          const time = new Date(p.value[0]);
          const count = p.value[2] || 1;
          return `${time.toLocaleString()}<br/>Count: ${count}`;
        },
      },
      xAxis: { type: 'time', scale: true },
      yAxis: { type: 'category', data: tracks },
      dataZoom: [
        {
          type: 'slider',
          xAxisIndex: 0,
          filterMode: 'none',
          minValueSpan: 1000,
          maxValueSpan: yearMs,
        },
        { type: 'inside', xAxisIndex: 0, minValueSpan: 1000, maxValueSpan: yearMs },
      ],
      brush: {
        xAxisIndex: 'all',
        brushLink: 'all',
        throttleType: 'debounce',
        throttleDelay: 300,
        toolbox: ['rect', 'keep', 'clear'],
      },
      series,
    }),
    [tracks, series],
  );

  const onEvents = {
    dataZoom: (params: any) => {
      if (params.batch && params.batch[0]) {
        const { startValue, endValue } = params.batch[0];
        setViewRange([startValue, endValue]);
      }
    },
    brushselected: (params: any) => {
      const area = params.batch?.[0]?.areas?.[0];
      if (area) {
        const [start, end] = area.coordRange as [number, number];
        setSelectedRange([start, end]);
        const ids = events
          .filter((e) => {
            const t = +new Date(e.timestamp);
            return t >= start && t <= end;
          })
          .map((e) => e.id);
        setSelectedThreats(ids);
      }
    },
  };

  return (
    <ReactECharts
      ref={chartRef}
      option={option}
      onEvents={onEvents}
      style={{ height: 300, width: '100%' }}
    />
  );
};

export default ThreatTimeline;

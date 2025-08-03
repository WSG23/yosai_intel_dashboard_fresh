import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import * as d3 from 'd3';
import { subscribeToAccessStream, AccessEvent } from '../../services/realtime';

type Range = '24h' | 'week' | 'month';

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN || '';

const AccessPatternHeatmap: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [range, setRange] = useState<Range>('24h');
  const eventsRef = useRef<AccessEvent[]>([]);

  // initialize map and svg overlay
  useEffect(() => {
    if (mapContainer.current && !mapRef.current) {
      mapRef.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/light-v10',
        center: [0, 0],
        zoom: 15,
      });
      mapRef.current.on('load', () => {
        svgRef.current = d3
          .select(mapRef.current!.getCanvasContainer())
          .append('svg')
          .attr('class', 'pointer-events-none absolute inset-0')
          .node() as SVGSVGElement;
        draw();
      });
    }
    return () => {
      mapRef.current?.remove();
    };
  }, []);

  // subscribe to realtime events
  useEffect(() => {
    const unsubscribe = subscribeToAccessStream((evt) => {
      eventsRef.current = [...eventsRef.current, evt];
      draw();
    });
    return unsubscribe;
  }, [range]);

  // redraw on map move
  useEffect(() => {
    if (!mapRef.current) return;
    const redraw = () => draw();
    mapRef.current.on('move', redraw);
    return () => {
      mapRef.current?.off('move', redraw);
    };
  }, []);

  const filterEvents = (): AccessEvent[] => {
    const now = Date.now();
    const dur =
      range === '24h'
        ? 24 * 60 * 60 * 1000
        : range === 'week'
          ? 7 * 24 * 60 * 60 * 1000
          : 30 * 24 * 60 * 60 * 1000;
    return eventsRef.current.filter(
      (e) => now - new Date(e.timestamp).getTime() <= dur,
    );
  };

  const draw = () => {
    if (!svgRef.current || !mapRef.current) return;
    const map = mapRef.current;
    const data = filterEvents();
    const project = (d: AccessEvent) => map.project([d.lng, d.lat]);
    const svg = d3.select(svgRef.current);

    const circles = svg
      .selectAll<SVGCircleElement, AccessEvent>('circle')
      .data(data, (d: any) => d.id);

    const enter = circles
      .enter()
      .append('circle')
      .attr('r', 0)
      .attr('cx', (d) => project(d).x)
      .attr('cy', (d) => project(d).y)
      .style('fill', 'rgba(0,123,255,0.6)')
      .style('filter', (d) => (d.anomaly ? 'drop-shadow(0 0 6px red)' : 'none'))
      .on('click', (_evt, d) => {
        new mapboxgl.Popup()
          .setLngLat([d.lng, d.lat])
          .setHTML(`<strong>${d.id}</strong>`)
          .addTo(map);
      });

    enter
      .transition()
      .duration(500)
      .attr('r', (d) => 5 + d.count);

    circles
      .merge(enter as any)
      .transition()
      .duration(500)
      .attr('cx', (d) => project(d).x)
      .attr('cy', (d) => project(d).y);

    circles.exit().transition().duration(300).attr('r', 0).remove();
  };

  return (
    <div className="relative w-full h-full">
      <div className="absolute top-2 left-2 z-10 bg-white rounded shadow p-2 space-x-2">
        {(['24h', 'week', 'month'] as Range[]).map((r) => (
          <button
            key={r}
            onClick={() => {
              setRange(r);
              draw();
            }}
            className={`px-2 py-1 text-sm rounded ${
              range === r ? 'bg-blue-500 text-white' : 'bg-gray-200'
            }`}
          >
            {r === '24h' ? '24 hr' : r === 'week' ? 'Weekly' : 'Monthly'}
          </button>
        ))}
      </div>
      <div ref={mapContainer} className="w-full h-full" />
    </div>
  );
};

export default AccessPatternHeatmap;

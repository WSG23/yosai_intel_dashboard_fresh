import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import { subscribeToAccessStream, AccessEvent } from '../../services/realtime';

type Range = '24h' | 'week' | 'month';

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN || '';

const AccessPatternHeatmap: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const [range, setRange] = useState<Range>('24h');
  const eventsRef = useRef<AccessEvent[]>([]);

  // initialize map and layers
  useEffect(() => {
    if (mapContainer.current && !mapRef.current) {
      mapRef.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/light-v10',
        center: [0, 0],
        zoom: 15,
      });
      mapRef.current.on('load', () => {
        mapRef.current!.addSource('events', {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: [] },
        });
        mapRef.current!.addLayer({
          id: 'events',
          type: 'circle',
          source: 'events',
          paint: {
            'circle-radius': ['+', 4, ['get', 'count']],
            'circle-color': 'rgba(0,123,255,0.6)',
            'circle-stroke-color': [
              'case',
              ['get', 'anomaly'],
              'red',
              'transparent',
            ],
            'circle-stroke-width': 2,
          },
        });
        mapRef.current!.on('click', 'events', (e) => {
          const feature = e.features?.[0];
          if (feature) {
            new mapboxgl.Popup()
              .setLngLat(feature.geometry.coordinates as mapboxgl.LngLatLike)
              .setHTML(`<strong>${feature.properties?.id}</strong>`)
              .addTo(mapRef.current!);
          }
        });
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
    if (!mapRef.current) return;
    const data = {
      type: 'FeatureCollection' as const,
      features: filterEvents().map((e) => ({
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: [e.lng, e.lat] },
        properties: { id: e.id, count: e.count, anomaly: e.anomaly },
      })),
    };
    const source = mapRef.current.getSource('events') as mapboxgl.GeoJSONSource;
    if (source) {
      source.setData(data);
    }
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

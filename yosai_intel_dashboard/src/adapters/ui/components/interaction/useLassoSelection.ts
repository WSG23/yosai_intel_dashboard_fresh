import { useState, useRef, useCallback } from 'react';
import { Polygon } from './lasso';

export const useLassoSelection = () => {
  const [polygon, setPolygon] = useState<Polygon>([]);
  const drawing = useRef(false);

  const start = useCallback((x: number, y: number) => {
    drawing.current = true;
    setPolygon([{ x, y }]);
  }, []);

  const move = useCallback((x: number, y: number) => {
    if (drawing.current) {
      setPolygon((poly) => [...poly, { x, y }]);
    }
  }, []);

  const end = useCallback(() => {
    drawing.current = false;
  }, []);

  const reset = useCallback(() => setPolygon([]), []);

  const handlers = {
    onPointerDown: (e: React.PointerEvent) => start(e.clientX, e.clientY),
    onPointerMove: (e: React.PointerEvent) => move(e.clientX, e.clientY),
    onPointerUp: end,
    onTouchStart: (e: React.TouchEvent) => {
      const t = e.touches[0];
      start(t.clientX, t.clientY);
    },
    onTouchMove: (e: React.TouchEvent) => {
      const t = e.touches[0];
      move(t.clientX, t.clientY);
    },
    onTouchEnd: end,
  };

  return { polygon, handlers, reset };
};

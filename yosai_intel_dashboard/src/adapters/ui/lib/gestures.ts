import { useEffect, useRef } from 'react';

export type SwipeDir = 'left' | 'right' | 'up' | 'down';

export const useSwipe = (onSwipe: (dir: SwipeDir) => void) => {
  const ref = useRef<HTMLElement | null>(null);
  const start = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const handleStart = (e: TouchEvent) => {
      const touch = e.touches[0];
      start.current = { x: touch.clientX, y: touch.clientY };
    };

    const handleEnd = (e: TouchEvent) => {
      if (!start.current) return;
      const touch = e.changedTouches[0];
      const dx = touch.clientX - start.current.x;
      const dy = touch.clientY - start.current.y;

      if (Math.abs(dx) > Math.abs(dy)) {
        onSwipe(dx > 0 ? 'right' : 'left');
      } else {
        onSwipe(dy > 0 ? 'down' : 'up');
      }
      start.current = null;
    };

    node.addEventListener('touchstart', handleStart);
    node.addEventListener('touchend', handleEnd);

    return () => {
      node.removeEventListener('touchstart', handleStart);
      node.removeEventListener('touchend', handleEnd);
    };
  }, [onSwipe]);

  return ref;
};

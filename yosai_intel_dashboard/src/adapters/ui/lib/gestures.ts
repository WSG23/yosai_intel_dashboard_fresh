import { useEffect, useRef } from 'react';
import Hammer from 'hammerjs';

type SwipeDir = 'left' | 'right' | 'up' | 'down';

export const useSwipe = (onSwipe: (dir: SwipeDir) => void) => {
  const ref = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const hammer = new Hammer(ref.current);
    hammer.get('swipe').set({ direction: Hammer.DIRECTION_ALL });
    const handler = (ev: any) => {
      switch (ev.direction) {
        case Hammer.DIRECTION_LEFT:
          onSwipe('left');
          break;
        case Hammer.DIRECTION_RIGHT:
          onSwipe('right');
          break;
        case Hammer.DIRECTION_UP:
          onSwipe('up');
          break;
        case Hammer.DIRECTION_DOWN:
          onSwipe('down');
          break;
      }
    };
    hammer.on('swipe', handler);
    return () => {
      hammer.off('swipe', handler);
      hammer.destroy();
    };
  }, [onSwipe]);

  return ref;
};

export const usePinch = (onPinch: (scale: number) => void) => {
  const ref = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const hammer = new Hammer(ref.current);
    hammer.get('pinch').set({ enable: true });
    const handler = (ev: any) => onPinch(ev.scale);
    hammer.on('pinch', handler);
    return () => {
      hammer.off('pinch', handler);
      hammer.destroy();
    };
  }, [onPinch]);

  return ref;
};

export const useLongPress = (onPress: () => void, time = 500) => {
  const ref = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const hammer = new Hammer(ref.current);
    hammer.get('press').set({ time });
    const handler = () => onPress();
    hammer.on('press', handler);
    return () => {
      hammer.off('press', handler);
      hammer.destroy();
    };
  }, [onPress, time]);

  return ref;
};


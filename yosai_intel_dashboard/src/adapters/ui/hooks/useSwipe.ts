import { useEffect } from 'react';
import { getGestureManager } from '../lib/gestures';

export default function useSwipe(handler: (ev: HammerInput) => void) {
  useEffect(() => {
    const manager = getGestureManager();
    manager.on('swipe', handler);
    return () => {
      manager.off('swipe', handler);
    };
  }, [handler]);
}

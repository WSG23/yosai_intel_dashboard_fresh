import { useEffect } from 'react';
import { getGestureManager } from '../lib/gestures';

export default function usePinch(handler: (ev: HammerInput) => void) {
  useEffect(() => {
    const manager = getGestureManager();
    manager.on('pinch', handler);
    return () => {
      manager.off('pinch', handler);
    };
  }, [handler]);
}

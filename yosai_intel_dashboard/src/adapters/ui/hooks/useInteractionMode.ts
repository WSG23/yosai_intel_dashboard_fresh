import { useEffect, useState } from 'react';

export type InteractionMode = 'pointer' | 'touch';

/**
 * Detects the primary user interaction mode (touch vs. pointer)
 * and toggles power-intensive features via a body class.
 */
const useInteractionMode = () => {
  const [mode, setMode] = useState<InteractionMode>('pointer');

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const enableTouch = () => setMode('touch');
    const enablePointer = () => setMode('pointer');

    window.addEventListener('touchstart', enableTouch, { once: true });
    window.addEventListener('mousemove', enablePointer, { once: true });

    return () => {
      window.removeEventListener('touchstart', enableTouch);
      window.removeEventListener('mousemove', enablePointer);
    };
  }, []);

  useEffect(() => {
    if (typeof document === 'undefined') return;

    const cls = 'power-features';
    if (mode === 'pointer') {
      document.body.classList.add(cls);
    } else {
      document.body.classList.remove(cls);
    }
  }, [mode]);

  return mode;
};

export default useInteractionMode;

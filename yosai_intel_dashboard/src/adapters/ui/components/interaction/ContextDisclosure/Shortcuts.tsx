import { useEffect } from 'react';

export const useContextDisclosureShortcuts = (
  expand: () => void,
  collapse: () => void
) => {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'e') {
        expand();
      }
      if (e.key === 'Escape') {
        collapse();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [expand, collapse]);
};

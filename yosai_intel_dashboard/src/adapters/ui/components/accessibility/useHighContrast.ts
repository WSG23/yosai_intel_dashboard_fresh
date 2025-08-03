import { useEffect } from 'react';

export const useHighContrast = () => {
  useEffect(() => {
    if (window.matchMedia && window.matchMedia('(prefers-contrast: more)').matches) {
      document.body.classList.add('high-contrast');
    }
  }, []);
};

export default useHighContrast;

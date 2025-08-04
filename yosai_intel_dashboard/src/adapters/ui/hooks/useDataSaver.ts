import { useEffect, useState } from 'react';

/**
 * Detect if the user has enabled data saver mode or is on a slow connection.
 */
export function useDataSaver() {
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    const connection = (navigator as any).connection;
    if (connection) {
      if (connection.saveData) {
        setEnabled(true);
        return;
      }
      const slowTypes = ['slow-2g', '2g'];
      if (slowTypes.includes(connection.effectiveType)) {
        setEnabled(true);
      }
    }
  }, []);

  return enabled;
}

export default useDataSaver;

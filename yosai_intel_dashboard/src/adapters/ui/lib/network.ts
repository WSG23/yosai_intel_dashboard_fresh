import { useEffect, useState } from 'react';

export interface NetworkStatus {
  online: boolean;
  saveData: boolean;
  effectiveType?: string;
}

/**
 * Reads the current network information from the browser.
 */
export function readNetworkStatus(): NetworkStatus {
  const nav: any = typeof navigator !== 'undefined' ? navigator : {};
  const connection = nav.connection || nav.mozConnection || nav.webkitConnection;
  return {
    online: nav.onLine ?? true,
    saveData: Boolean(connection?.saveData),
    effectiveType: connection?.effectiveType,
  };
}

/**
 * React hook that subscribes to changes in network status.
 */
export function useNetworkStatus(): NetworkStatus {
  const [status, setStatus] = useState<NetworkStatus>(readNetworkStatus());

  useEffect(() => {
    const update = () => setStatus(readNetworkStatus());
    const nav: any = typeof navigator !== 'undefined' ? navigator : {};
    const connection = nav.connection || nav.mozConnection || nav.webkitConnection;

    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    connection?.addEventListener?.('change', update);

    return () => {
      window.removeEventListener('online', update);
      window.removeEventListener('offline', update);
      connection?.removeEventListener?.('change', update);
    };
  }, []);

  return status;
}

import { useCallback, useState } from 'react';
import { authenticate, isAvailable } from '../../plugins/auth';

/** Hook to perform biometric authentication via Capacitor. */
export const useBiometricAuth = () => {
  const [available, setAvailable] = useState<boolean | null>(null);

  const checkAvailability = useCallback(async () => {
    const result = await isAvailable();
    setAvailable(result);
    return result;
  }, []);

  const verify = useCallback(async () => authenticate(), []);

  return { available, checkAvailability, verify };
};


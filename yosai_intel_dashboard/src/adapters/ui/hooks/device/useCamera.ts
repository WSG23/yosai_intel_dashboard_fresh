import { useCallback } from 'react';
import { scan, CameraScan } from '../../plugins/camera';

/** Hook providing access to the device camera. */
export const useCamera = () => {
  const scanPhoto = useCallback(async (): Promise<CameraScan> => scan(), []);

  return { scanPhoto };
};


import { useCallback, useEffect, useState } from 'react';
import { getLocation, Coordinates } from '../../plugins/location';

/** Hook that retrieves and tracks the device's current location. */
export const useLocation = () => {
  const [coords, setCoords] = useState<Coordinates | null>(null);

  const update = useCallback(async () => {
    const current = await getLocation();
    setCoords(current);
  }, []);

  useEffect(() => {
    void update();
  }, [update]);

  return { coords, update };
};


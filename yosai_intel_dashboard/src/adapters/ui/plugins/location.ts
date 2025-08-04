import { Geolocation, Position } from '@capacitor/geolocation';

export interface Coordinates {
  latitude: number;
  longitude: number;
}

/** Retrieve the device's current GPS coordinates. */
export const getLocation = async (): Promise<Coordinates> => {
  const pos: Position = await Geolocation.getCurrentPosition();

  return {
    latitude: pos.coords.latitude,
    longitude: pos.coords.longitude,
  };
};


export interface Point {
  x: number;
  y: number;
  [key: string]: any;
}

export type Polygon = { x: number; y: number }[];

export const isPointInPolygon = (point: Point, polygon: Polygon) => {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].x, yi = polygon[i].y;
    const xj = polygon[j].x, yj = polygon[j].y;
    const intersect =
      yi > point.y !== yj > point.y &&
      point.x < ((xj - xi) * (point.y - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
};

export const lassoSelect = (points: Point[], polygon: Polygon) =>
  points.filter((p) => isPointInPolygon(p, polygon));

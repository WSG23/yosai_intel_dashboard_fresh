import { calculateROI } from '../../../../../analytics/metrics/roi';

describe('calculateROI', () => {
  it('returns 0 when cost is 0', () => {
    expect(calculateROI(100, 0)).toBe(0);
  });

  it('returns 0 when cost is negative', () => {
    expect(calculateROI(100, -50)).toBe(0);
  });
});


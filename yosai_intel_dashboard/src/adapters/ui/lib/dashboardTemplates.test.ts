import { saveTemplate, loadTemplate, combineChartData, ChartTemplate } from './dashboardTemplates';

describe('dashboard templates utilities', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('save and load template', () => {
    const layout: ChartTemplate[] = [{ id: '1', type: 'Line', x: 0, y: 0, w: 100, h: 100 }];
    saveTemplate('test', layout);
    expect(loadTemplate('test')).toEqual(layout);
  });

  test('combine chart data', () => {
    const result = combineChartData([[1,2,3],[4,5],[6]]);
    expect(result).toEqual([11,7,3]);
  });
});

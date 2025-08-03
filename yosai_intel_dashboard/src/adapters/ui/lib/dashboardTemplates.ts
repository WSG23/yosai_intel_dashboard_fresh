export interface ChartTemplate {
  id: string;
  type: string;
  x: number;
  y: number;
  w: number;
  h: number;
  data?: number[];
}

const TEMPLATE_PREFIX = 'dashboard_template_';

export function saveTemplate(name: string, layout: ChartTemplate[]) {
  localStorage.setItem(`${TEMPLATE_PREFIX}${name}`, JSON.stringify(layout));
}

export function loadTemplate(name: string): ChartTemplate[] | null {
  const raw = localStorage.getItem(`${TEMPLATE_PREFIX}${name}`);
  return raw ? (JSON.parse(raw) as ChartTemplate[]) : null;
}

// Combine multiple chart data arrays by index
export function combineChartData(dataSets: number[][]): number[] {
  const max = Math.max(0, ...dataSets.map((d) => d.length));
  const result: number[] = Array(max).fill(0);
  dataSets.forEach((set) => {
    set.forEach((value, i) => {
      result[i] += value;
    });
  });
  return result;
}

import { api } from './client';

export interface AvailableChart {
  type: string;
  name: string;
  description: string;
}

export const graphsAPI = {
  async getAvailableCharts(): Promise<AvailableChart[]> {
    const res = await api.get<{ charts: AvailableChart[] }>('/graphs/available-charts');
    return res.charts;
  },

  async getChartData(chartType: string): Promise<any> {
    const res = await api.get<{ type: string; data: any }>(`/graphs/chart/${chartType}`);
    return res.data;
  },
};

export default graphsAPI;

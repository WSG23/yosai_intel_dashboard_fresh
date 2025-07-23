import { ReportHandler } from 'web-vitals';
import { log } from './logger';

const reportWebVitals = (onPerfEntry?: ReportHandler) => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      const handler: ReportHandler = metric => {
        log('info', 'web-vital', { name: metric.name, value: metric.value });
        onPerfEntry(metric);
      };
      getCLS(handler);
      getFID(handler);
      getFCP(handler);
      getLCP(handler);
      getTTFB(handler);
    });
  }
};

export default reportWebVitals;

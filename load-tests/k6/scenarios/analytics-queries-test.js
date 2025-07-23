import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    analytics: {
      executor: 'constant-arrival-rate',
      rate: 50,
      timeUnit: '1s',
      duration: '1m',
      preAllocatedVUs: 20,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

export default function () {
  const res = http.get('http://localhost:8001/analytics?q=latest');
  check(res, { 'status is 200': (r) => r.status === 200 });
}

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    soak: {
      executor: 'constant-arrival-rate',
      rate: 1000,
      timeUnit: '1s',
      duration: '30m',
      preAllocatedVUs: 1000,
      maxVUs: 1000,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<750', 'p(99)<1500'],
  },
};

export default function () {
  const res = http.get('http://localhost:8000/health');
  check(res, { ok: (r) => r.status === 200 });
  sleep(1);
}

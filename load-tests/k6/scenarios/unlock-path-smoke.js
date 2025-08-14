import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 10,
  duration: '2m',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<100'],
  },
};

export default function () {
  const res = http.get('http://localhost:8080/unlock');
  check(res, { 'status is 200': (r) => r.status === 200 });
}

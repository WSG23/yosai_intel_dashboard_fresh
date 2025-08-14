import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 20,
  duration: '2m',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<100'],
  },
};

export default function () {
  const url = `${__ENV.BASE_URL || 'http://localhost:8080'}/unlock`;
  const payload = JSON.stringify({
    userId: `user-${__VU}`,
    resource: `/path/${__ITER}`,
    action: 'unlock',
  });
  const params = { headers: { 'Content-Type': 'application/json' } };
  const res = http.post(url, payload, params);
  check(res, { 'status is 200': (r) => r.status === 200 });
}

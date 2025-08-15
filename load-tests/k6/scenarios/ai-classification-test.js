import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
};

export default function () {
  const baseUrl = __ENV.TARGET_URL || 'http://localhost:8050';
  const res = http.get(`${baseUrl}/health`);
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(1);
}

import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    ingestion: {
      executor: 'constant-arrival-rate',
      rate: 100000,
      timeUnit: '1s',
      duration: '10s',
      preAllocatedVUs: 2000,
      maxVUs: 2000,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const payload = JSON.stringify({ deviceId: __VU, ts: Date.now(), value: 1 });
  const params = { headers: { 'Content-Type': 'application/json' } };
  const res = http.post('http://localhost:8000/events', payload, params);
  check(res, { 'accepted': (r) => r.status === 202 });
}

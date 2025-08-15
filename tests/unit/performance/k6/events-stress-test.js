import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    stress: {
      executor: 'constant-arrival-rate',
      rate: 100000,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 10000,
      maxVUs: 10000,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
  },
};

export default function () {
  const payload = JSON.stringify({
    deviceId: __VU,
    ts: Date.now(),
    eventType: 'granted',
  });
  const params = { headers: { 'Content-Type': 'application/json' } };
  const res = http.post('http://localhost:8000/events', payload, params);
  check(res, { accepted: (r) => r.status === 202 });
}

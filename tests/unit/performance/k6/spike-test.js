import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  scenarios: {
    spike: {
      executor: 'ramping-arrival-rate',
      startRate: 1000,
      timeUnit: '1s',
      preAllocatedVUs: 1000,
      stages: [
        { target: 20000, duration: '10s' },
        { target: 20000, duration: '20s' },
        { target: 0, duration: '10s' },
      ],
    },
  },
};

export default function () {
  const res = http.get('http://localhost:8000/health');
  check(res, { ok: (r) => r.status === 200 });
  sleep(1);
}

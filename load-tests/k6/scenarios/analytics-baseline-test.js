import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    analytics: {
      executor: 'constant-arrival-rate',
      rate: 10,
      timeUnit: '1s',
      duration: '30s',
      preAllocatedVUs: 5,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

export default function () {
  const baseUrl = 'http://localhost:8000';
  check(http.get(`${baseUrl}/health`), { 'health ok': (r) => r.status === 200 });
  check(http.get(`${baseUrl}/api/v1/analytics/dashboard-summary`), { 'dashboard ok': (r) => r.status === 200 });
  check(http.get(`${baseUrl}/api/v1/analytics/access-patterns`), { 'access ok': (r) => r.status === 200 });
  check(http.get(`${baseUrl}/api/v1/analytics/threat_assessment`), { 'threat ok': (r) => r.status === 200 });
}

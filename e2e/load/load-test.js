import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 50 },   // Stay at 50 users
    { duration: '30s', target: 100 }, // Ramp up to 100 users
    { duration: '1m', target: 100 }, // Stay at 100 users
    { duration: '30s', target: 200 }, // Ramp up to 200 users
    { duration: '1m', target: 200 }, // Stay at 200 users
    { duration: '30s', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.1'],    // Error rate must be below 10%
  },
};

const BASE_URL = 'http://127.0.0.1:8000';

export default function() {
  // Test 1: Get windows endpoint
  let response = http.get(`${BASE_URL}/v1/energyhub/windows`);
  check(response, {
    'windows endpoint status is 200': (r) => r.status === 200,
    'windows response time < 200ms': (r) => r.timings.duration < 200,
    'windows response has data': (r) => JSON.parse(r.body).length > 0,
  });

  sleep(1);

  // Test 2: Start a charge session
  const startPayload = JSON.stringify({
    user_id: `test-user-${__VU}-${__ITER}`,
    hub_id: 'hub_domain_a'
  });

  response = http.post(`${BASE_URL}/v1/energyhub/events/charge-start`, startPayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(response, {
    'charge start status is 200': (r) => r.status === 200,
    'charge start response time < 300ms': (r) => r.timings.duration < 300,
    'charge start has session_id': (r) => JSON.parse(r.body).session_id !== undefined,
  });

  const sessionId = JSON.parse(response.body).session_id;

  sleep(1);

  // Test 3: Stop the charge session
  const stopPayload = JSON.stringify({
    session_id: sessionId,
    kwh_consumed: Math.random() * 20 + 5 // Random kWh between 5-25
  });

  response = http.post(`${BASE_URL}/v1/energyhub/events/charge-stop`, stopPayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(response, {
    'charge stop status is 200': (r) => r.status === 200,
    'charge stop response time < 500ms': (r) => r.timings.duration < 500,
    'charge stop has reward data': (r) => JSON.parse(r.body).total_reward_usd !== undefined,
  });

  sleep(1);

  // Test 4: Health check
  response = http.get(`${BASE_URL}/healthz`);
  check(response, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 100ms': (r) => r.timings.duration < 100,
  });

  sleep(1);

  // Test 5: Readiness check
  response = http.get(`${BASE_URL}/readyz`);
  check(response, {
    'readiness check status is 200': (r) => r.status === 200,
    'readiness check response time < 200ms': (r) => r.timings.duration < 200,
  });

  sleep(1);

  // Test 6: Metrics endpoint
  response = http.get(`${BASE_URL}/metrics`);
  check(response, {
    'metrics endpoint status is 200': (r) => r.status === 200,
    'metrics response time < 100ms': (r) => r.timings.duration < 100,
    'metrics contains prometheus data': (r) => r.body.includes('http_requests_total'),
  });
}

export function handleSummary(data) {
  return {
    'load-test-results.json': JSON.stringify(data, null, 2),
    'load-test-results.html': htmlReport(data),
  };
}

function htmlReport(data) {
  return `
    <html>
      <head><title>Load Test Results</title></head>
      <body>
        <h1>Load Test Results</h1>
        <h2>Summary</h2>
        <p>Total Requests: ${data.metrics.http_reqs.count}</p>
        <p>Failed Requests: ${data.metrics.http_req_failed.count}</p>
        <p>Average Response Time: ${data.metrics.http_req_duration.avg}ms</p>
        <p>95th Percentile: ${data.metrics.http_req_duration.p95}ms</p>
        <p>99th Percentile: ${data.metrics.http_req_duration.p99}ms</p>
      </body>
    </html>
  `;
}

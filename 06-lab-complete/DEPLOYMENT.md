# Deployment Information

## Public URL
`https://mellow-reprieve-production-3e08.up.railway.app`

## Platform
Railway.

## Test Commands

## Local Docker Verification

### Health Check
```bash
curl http://localhost:8000/health
```

Result:
```json
{"status":"ok","version":"1.0.0","environment":"staging","uptime_seconds":7.2,"total_requests":2,"checks":{"llm":"mock"},"timestamp":"2026-06-12T09:16:26.155464+00:00"}
```

### Readiness Check
```bash
curl http://localhost:8000/ready
```

Result:
```json
{"ready":true}
```

### Authentication Required
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'
```

Result:
```json
{"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}
```

### API Test With Authentication
```bash
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello final project"}'
```

Result:
```json
{"question":"Hello final project","answer":"I am a cloud-ready AI agent. The deployment pipeline is working.","model":"gpt-4o-mini","timestamp":"2026-06-12T09:16:26.364398+00:00"}
```

## Public Deployment Verification

### Health Check
```bash
curl https://mellow-reprieve-production-3e08.up.railway.app/health
```

Expected result includes:
```json
{"status":"ok"}
```

Actual result:
```json
{"status":"ok","version":"1.0.0","environment":"production","uptime_seconds":24.9,"total_requests":2,"checks":{"llm":"mock"},"timestamp":"2026-06-12T09:33:03.859925+00:00"}
```

### Authentication Required
```bash
curl -X POST https://mellow-reprieve-production-3e08.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'
```

Expected: `401 Unauthorized`.

Actual result:
```json
{"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}
```

### API Test With Authentication
```bash
curl -X POST https://mellow-reprieve-production-3e08.up.railway.app/ask \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello from production"}'
```

Expected: `200 OK` with an answer.

Actual result:
```json
{"question":"Hello final production","answer":"The agent is running correctly. Your request was received and processed.","model":"gpt-4o-mini","timestamp":"2026-06-12T09:33:05.600905+00:00"}
```

### Rate Limit Test
```bash
for i in {1..15}; do
  curl -X POST https://mellow-reprieve-production-3e08.up.railway.app/ask \
    -H "X-API-Key: YOUR_AGENT_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"question":"rate limit test"}'
done
```

Expected: after 10 requests/minute, the service returns `429`.

## Environment Variables Set
- `PORT`
- `REDIS_URL`
- `AGENT_API_KEY`
- `JWT_SECRET`
- `ENVIRONMENT=production`
- `RATE_LIMIT_PER_MINUTE=10`
- `MONTHLY_BUDGET_USD=10.0`
- `OPENAI_API_KEY` optional, because the app can run with mock LLM.

## Screenshots
- Deployment dashboard: [deployment-dashboard.png](../screenshots/deployment-dashboard.png)
- Service running: [service-running.png](../screenshots/service-running.png)
- Test results: [test-results.png](../screenshots/test-results.png)

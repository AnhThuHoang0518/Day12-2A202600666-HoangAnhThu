# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Phát hiện anti-patterns

Trong `01-localhost-vs-production/develop/app.py`, em tìm thấy các vấn đề sau:

1. API key và database URL bị hardcode trực tiếp trong code.
2. Secret bị in ra log bằng `print()`, dễ bị lộ khi xem log.
3. Không có cơ chế config management, các giá trị như `DEBUG` và `MAX_TOKENS` được đặt cứng.
4. Không có endpoint `/health`, nên cloud platform không biết app còn sống hay đã lỗi.
5. Host và port bị hardcode là `localhost:8000`, không phù hợp khi deploy lên Railway/Render vì platform inject port qua environment variable.
6. `reload=True` được bật trực tiếp, phù hợp local dev nhưng không nên dùng trong production.
7. Không có graceful shutdown, khi container bị tắt thì request đang xử lý có thể bị ngắt đột ngột.

### Exercise 1.2: Chạy basic version

Basic version có thể chạy local và trả lời request, nhưng chưa production-ready vì còn hardcoded secrets, không có health check, log chưa chuẩn, port cố định và không xử lý shutdown.

### Exercise 1.3: So sánh với advanced version

| Feature | Basic | Advanced | Tại sao quan trọng? |
|---------|-------|----------|---------------------|
| Config | Hardcode | Env vars | Không để lộ secrets trong code, dễ đổi cấu hình giữa local/staging/production |
| Health check | Không có | Có `/health` và `/ready` | Cloud platform/load balancer biết app còn sống và đã sẵn sàng nhận traffic |
| Logging | `print()` | JSON structured logs | Dễ đọc, lọc, search và debug trên cloud logging tools |
| Shutdown | Đột ngột | Graceful shutdown với lifespan và SIGTERM | Cho request đang chạy hoàn thành và cleanup tài nguyên trước khi container tắt |
| Host/Port | `localhost:8000` hardcode | `HOST`/`PORT` từ env, bind `0.0.0.0` | Chạy được trong Docker/Railway/Render vì platform inject `PORT` |
| Debug mode | `reload=True` | Theo biến `DEBUG` | Tránh bật debug/reload trong production |
| Secrets | Hardcode và có thể bị log ra | Đọc từ env, không log secret | Giảm rủi ro lộ key khi push code hoặc xem log |

## Part 2: Docker Containerization

### Exercise 2.1: Dockerfile cơ bản

1. Base image là `python:3.11`.
2. Working directory là `/app`.
3. `COPY requirements.txt` được đặt trước bước copy source code để tận dụng Docker layer cache. Khi chỉ sửa code mà không đổi dependencies, Docker không cần cài lại package.
4. `CMD` là command mặc định khi container start và có thể bị override lúc `docker run`. `ENTRYPOINT` thường dùng để cố định executable chính của container; arguments từ `docker run` sẽ được truyền vào entrypoint.

### Exercise 2.2: Build và run

Lệnh build basic image:

```bash
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .
```

Lệnh run:

```bash
docker run -p 8000:8000 my-agent:develop
```

Lệnh test:

```bash
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

Image size:

- `my-agent:develop`: disk usage `1.66GB`, content size `424MB`

Nhận xét: image develop dùng `python:3.11` full image nên thường lớn hơn production image.

### Exercise 2.3: Multi-stage build

- Stage 1 (`builder`): dùng `python:3.11-slim`, cài build tools như `gcc`, `libpq-dev`, sau đó cài dependencies vào `/root/.local`.
- Stage 2 (`runtime`): dùng image runtime sạch hơn, chỉ copy dependencies đã cài từ builder và copy source code cần chạy.
- Image nhỏ hơn vì runtime stage không giữ lại build tools, apt cache và các file chỉ cần trong quá trình build.
- Production Dockerfile cũng tạo non-root user `appuser`, set `PYTHONPATH`, expose port, thêm `HEALTHCHECK`, và chạy app bằng `uvicorn` với `--workers 2`.

Image size:

- `my-agent:develop`: disk usage `1.66GB`, content size `424MB`
- `my-agent:advanced`: disk usage `236MB`, content size `56.6MB`
- So sánh: advanced image giảm từ `1.66GB` xuống `236MB`, tức nhỏ hơn khoảng `85.8%` theo disk usage. Content size giảm từ `424MB` xuống `56.6MB`, tức nhỏ hơn khoảng `86.7%`. Production image nhỏ hơn và an toàn hơn vì dùng multi-stage build, slim base image và non-root user.

### Exercise 2.4: Docker Compose stack

Các service trong `02-docker/production/docker-compose.yml`:

1. `agent`: FastAPI AI agent, build từ production Dockerfile.
2. `redis`: cache/session/rate limiting backend.
3. `qdrant`: vector database cho RAG.
4. `nginx`: reverse proxy và load balancer, expose cổng `80` và `443`.

Architecture diagram:

```text
Client
  |
  v
Nginx reverse proxy / load balancer
  |
  v
Agent service
  |-------------------|
  v                   v
Redis              Qdrant
```

Các service communicate qua Docker network `internal`. Client không gọi trực tiếp `agent`; request đi qua Nginx trước, sau đó Nginx route vào agent. Agent kết nối Redis bằng hostname `redis` và Qdrant bằng hostname `qdrant`.

## Part 3: Cloud Deployment

### Exercise 3.1: Deploy Railway

Các bước deploy Railway:

1. Cài Railway CLI bằng `npm i -g @railway/cli`.
2. Login bằng `railway login`.
3. Khởi tạo project bằng `railway init`.
4. Set biến môi trường như `PORT`, `AGENT_API_KEY`, `ENVIRONMENT`.
5. Deploy bằng `railway up`.
6. Lấy public URL bằng `railway domain`.

Kết quả test public URL:

- Public URL: `https://ideal-transformation-production-6cd8.up.railway.app/`
- Health check:

```json
{"status":"ok","uptime_seconds":66.1,"platform":"Railway","timestamp":"2026-06-12T08:43:41.041921+00:00"}
```

- Agent endpoint:

```json
{"question":"Hello from Railway","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.","platform":"Railway"}
```

### Exercise 3.2: So sánh `render.yaml` với `railway.toml`

| Tiêu chí | `render.yaml` | `railway.toml` |
|---------|---------------|----------------|
| Mục đích | Blueprint mô tả infrastructure trên Render | Config deploy cho Railway |
| Khai báo service | Khai báo rõ web service và Redis service | Chủ yếu khai báo build/deploy cho app |
| Build | Có `buildCommand` và `startCommand` | Có `builder` và `startCommand` |
| Health check | `healthCheckPath: /health` | `healthcheckPath = "/health"` |
| Env vars | Khai báo trong `envVars`, secret có thể `sync: false` hoặc `generateValue` | Đặt qua Railway Dashboard hoặc `railway variables set` |
| Auto deploy | Có `autoDeploy: true` | Railway deploy theo project/CLI hoặc integration |
| Redis | Có thể khai báo Redis service ngay trong blueprint | Thường thêm Redis bằng Railway service/plugin riêng |

Kết luận: Render dùng `render.yaml` như Infrastructure as Code đầy đủ hơn, có thể khai báo nhiều service trong một file. Railway dùng `railway.toml` gọn hơn, tập trung vào cách build, start, health check và restart policy của app.

### Exercise 3.3: GCP Cloud Run (Optional)

`cloudbuild.yaml` mô tả CI/CD pipeline: build container image, push image lên registry, rồi deploy lên Cloud Run. `service.yaml` mô tả cấu hình Cloud Run service như container image, port, env vars, resources và scaling. Phần này optional nên em chỉ đọc để hiểu pipeline.

## Part 4: API Security

### Exercise 4.1: API Key authentication

- API key được check trong function `verify_api_key()` của `04-api-gateway/develop/app.py`.
- Function này đọc header `X-API-Key` bằng `APIKeyHeader`.
- Endpoint `/ask` dùng `Depends(verify_api_key)`, nên request phải có key hợp lệ mới được xử lý.
- Nếu thiếu key, app trả về `401 Missing API key`.
- Nếu sai key, app trả về `403 Invalid API key`.
- Để rotate key, đổi biến môi trường `AGENT_API_KEY` trên server/cloud platform rồi restart hoặc redeploy service. Client phải dùng key mới trong header `X-API-Key`.

### Exercise 4.2: JWT authentication (Advanced)

JWT flow trong `04-api-gateway/production/auth.py`:

1. User gửi username/password để login.
2. App gọi `authenticate_user()` để kiểm tra credentials.
3. Nếu hợp lệ, app gọi `create_token()` để tạo JWT chứa `sub`, `role`, `iat`, `exp`.
4. Client gửi token trong header `Authorization: Bearer <token>`.
5. App gọi `verify_token()` để verify chữ ký và kiểm tra token expired/invalid.
6. Nếu token hợp lệ, app lấy được username và role từ payload để xử lý request.

JWT là stateless auth vì server không cần lưu session trong memory cho từng request; chỉ cần verify token bằng `JWT_SECRET`.

### Exercise 4.3: Rate limiting

- Algorithm được dùng: Sliding Window Counter.
- Mỗi user có một bucket lưu timestamp request trong `deque`.
- Window mặc định là `60` giây.
- Limit thường là `10 req/phút` cho user thường.
- Admin có limit cao hơn: `100 req/phút` trong `rate_limiter_admin`.
- Khi vượt limit, app trả về `429 Too Many Requests` kèm các header như `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`.
- Cách bypass/ưu tiên admin: kiểm tra role từ JWT. Nếu `role == "admin"` thì dùng `rate_limiter_admin`, còn user thường dùng `rate_limiter_user`.

### Exercise 4.4: Cost guard

Logic cost guard cần có:

1. Mỗi user có budget `$10/tháng`.
2. Spending được track theo key dạng `budget:{user_id}:{YYYY-MM}`.
3. Trước khi gọi LLM, lấy current spending từ Redis.
4. Nếu `current + estimated_cost > 10` thì trả về `False` hoặc raise lỗi `402`.
5. Nếu còn budget, cộng thêm cost bằng `incrbyfloat`.
6. Set TTL khoảng 32 ngày để tự reset sau khi sang tháng.

Implementation mẫu:

```python
import redis
from datetime import datetime

r = redis.Redis()

def check_budget(user_id: str, estimated_cost: float) -> bool:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"

    current = float(r.get(key) or 0)
    if current + estimated_cost > 10:
        return False

    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)
    return True
```

Trong final project, logic tương tự đã được đặt trong `app/cost_guard.py`, dùng Redis khi có `REDIS_URL` và fallback in-memory khi chạy local nhanh.

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks

Hai endpoint cần implement:

- `/health`: liveness probe, trả về `200` nếu process còn sống.
- `/ready`: readiness probe, kiểm tra dependency như Redis/database. Nếu dependency sẵn sàng thì trả về `200`; nếu chưa sẵn sàng thì trả về `503`.

Ví dụ logic:

```python
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    try:
        r.ping()
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="not ready")
```

Trong final project, `/health` và `/ready` đã được implement trong `app/main.py`.

### Exercise 5.2: Graceful shutdown

Graceful shutdown cần làm các bước:

1. Nhận signal `SIGTERM` từ container orchestrator.
2. Ngừng nhận request mới.
3. Cho request đang chạy hoàn thành.
4. Đóng connection đến Redis/database nếu có.
5. Ghi log shutdown và thoát sạch.

Trong final project, app dùng FastAPI lifespan để xử lý startup/shutdown và đăng ký handler cho `SIGTERM`.

### Exercise 5.3: Stateless design

Anti-pattern là lưu state trong memory, ví dụ `conversation_history = {}`. Khi scale nhiều instance, user có thể request vào instance khác và mất history.

Cách đúng là lưu state vào Redis:

- Conversation/session lưu theo key trong Redis.
- Bất kỳ instance nào cũng đọc được cùng một state.
- Khi restart container, state không phụ thuộc vào memory của một process.

Trong final project, rate limit và budget guard dùng Redis khi có `REDIS_URL`, giúp nhiều instance chia sẻ cùng state.

### Exercise 5.4: Load balancing

Khi chạy:

```bash
docker compose up --scale agent=3
```

Stack sẽ chạy nhiều instance `agent`. Nginx đứng trước để phân tán request đến các instance. Nếu một instance die, traffic vẫn có thể chuyển sang instance khác còn sống.

Quan sát cần ghi nhận:

- Có 3 agent instances được start.
- Requests được Nginx phân tán qua nhiều instance.
- Logs của agent cho thấy request không chỉ vào một container.

### Exercise 5.5: Test stateless

`test_stateless.py` kiểm tra:

1. Gọi API để tạo conversation/session.
2. Kill một instance bất kỳ.
3. Gọi tiếp request với cùng session.
4. Nếu history vẫn còn, nghĩa là state không phụ thuộc vào memory của instance đã chết.

Kết luận: Stateless design giúp app scale ngang và chịu lỗi tốt hơn.

## Part 6: Final Project

### Objective

Final project là một production-ready AI agent kết hợp tất cả concepts đã học: Docker, cloud deployment, auth, rate limiting, cost guard, health/readiness, graceful shutdown, stateless design và structured logging.

### Requirements mapping

| Requirement | File/Implementation |
|-------------|---------------------|
| Agent trả lời câu hỏi qua REST API | `app/main.py`, endpoint `POST /ask` |
| Dockerized với multi-stage build | `Dockerfile` |
| Config từ environment variables | `app/config.py` |
| API key authentication | `app/auth.py` |
| Rate limiting 10 req/min | `app/rate_limiter.py` |
| Cost guard $10/month | `app/cost_guard.py` |
| Health check endpoint | `GET /health` trong `app/main.py` |
| Readiness check endpoint | `GET /ready` trong `app/main.py` |
| Graceful shutdown | FastAPI lifespan và `SIGTERM` handler |
| Stateless design | Redis-backed rate limit/cost state |
| Structured JSON logging | JSON logs trong `app/main.py` |
| Deploy Railway/Render | `railway.toml` và `render.yaml` |

### Validation

Đã chạy production readiness checker:

```bash
py -3.11 -X utf8 check_production_ready.py
```

Kết quả:

```text
20/20 checks passed (100%)
PRODUCTION READY
```

Đã test local bằng Docker Compose:

```bash
docker compose up -d --build
```

Health check:

```json
{"status":"ok","version":"1.0.0","environment":"staging","uptime_seconds":7.2,"total_requests":2,"checks":{"llm":"mock"},"timestamp":"2026-06-12T09:16:26.155464+00:00"}
```

Readiness check:

```json
{"ready":true}
```

Request không có API key:

```json
{"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}
```

Request có API key:

```json
{"question":"Hello final project","answer":"I am a cloud-ready AI agent. The deployment pipeline is working.","model":"gpt-4o-mini","timestamp":"2026-06-12T09:16:26.364398+00:00"}
```

### Deployment result

- Public URL: `https://mellow-reprieve-production-3e08.up.railway.app`
- Platform: Railway
- Screenshot dashboard: [deployment-dashboard.png](screenshots/deployment-dashboard.png)
- Screenshot service running: [service-running.png](screenshots/service-running.png)
- Screenshot test result: [test-results.png](screenshots/test-results.png)

Public health check:

```json
{"status":"ok","version":"1.0.0","environment":"production","uptime_seconds":24.9,"total_requests":2,"checks":{"llm":"mock"},"timestamp":"2026-06-12T09:33:03.859925+00:00"}
```

Public readiness check:

```json
{"ready":true}
```

Public request không có API key:

```json
{"detail":"Invalid or missing API key. Include header: X-API-Key: <key>"}
```

Public request có API key:

```json
{"question":"Hello final production","answer":"The agent is running correctly. Your request was received and processed.","model":"gpt-4o-mini","timestamp":"2026-06-12T09:33:05.600905+00:00"}
```

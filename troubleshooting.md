# Investigation Journal & Troubleshooting Log

## Incident 1: NGINX Upstream 502 Bad Gateway
- **Symptom:** Curling `http://127.0.0.1:8080/ready` returned HTTP 502.
- **Root Cause:** NGINX configuration targeted `app-01:8081` and `app-02:8081`, whereas Flask backend instances listen on `8080`.
- **Resolution:** Corrected `upstream application_pool` in `nginx/nginx.conf` to target port `8080`.
- **Lesson Learned:** Always verify internal application listening ports (`APP_PORT`) against edge proxy upstream directives.

## Incident 2: Database & Redis Internal Port Mismatches (5433/6380 vs 5432/6379)
- **Symptom:** Application logs reported `OperationalError` when connecting to PostgreSQL and `ConnectionError` for Redis.
- **Root Cause:** `.env.example` configured `DATABASE_URL` with port `5433` and `REDIS_URL` with port `6380`, but container internal ports were `5432` and `6379`.
- **Resolution:** Updated `.env.example` to target standard internal ports `postgres:5432` and `redis:6379`.
- **Lesson Learned:** Distinguish between host port mappings and internal Docker bridge network container ports.

## Incident 3: Hardcoded Credentials in Configuration Templates
- **Symptom:** Plaintext passwords (`POSTGRES_PASSWORD`) were present in `.env.example`.
- **Root Cause:** Residual legacy authentication setup.
- **Resolution:** Stripped plaintext passwords, switched PostgreSQL to `POSTGRES_HOST_AUTH_METHOD=trust`, and enforced strict network boundary isolation (`internal: true`).

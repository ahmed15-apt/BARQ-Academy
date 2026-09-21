# BARQ Systems - Multi-Container Infrastructure Assessment & Automation

This repository contains the refactored, secure, and automated multi-container Docker Compose infrastructure stack for the BARQ Systems technical assessment.



## Technical Architecture & Request Flow

```
[ Client / Host Environment ]
              │
              │ (HTTP GET :8090)
              ▼
┌───────────────────────────┐
│        NGINX Proxy        │  <-- Bound to 127.0.0.1:8090 (frontend network)
└─────────────┬─────────────┘
              │
   ┌──────────┼──────────┐
   │ (Round-  │ (Round-  │ (Round-
   │  Robin)  │  Robin)  │  Robin)
   ▼          ▼          ▼
┌──────┐   ┌──────┐   ┌──────┐
│app-01│   │app-02│   │app-03│  <-- Flask APIs (UID 10001)
└───┬──┘   └───┬──┘   └───┬──┘
    │          │          │
    └──────────┼──────────┘
               │
               │ (backend network - internal: true)
               ▼
┌─────────────────────────────────────────┐
│ PostgreSQL (Port 5432)                  │
│  - Named Volume: postgres-data          │
│  - Auth: Isolated DB Credentials        │
├─────────────────────────────────────────┤
│ Redis Cache (Port 6379)                 │
└─────────────────────────────────────────┘
```




## Architecture & Configuration Summary

* **Ingress Port:** NGINX load balancer exposed on host port `8090` (configured via `PUBLIC_PORT` in `.env` with fallback default to `${PUBLIC_PORT:-8090}` in `docker-compose.yml`).
* **Horizontally Scaled Backends:** Three Flask API container instances (`app-01`, `app-02`, `app-03`) operating in an upstream round-robin load-balancing pool.
* **Strict Network Isolation:** PostgreSQL (`postgres:5432`) and Redis (`redis:6379`) are strictly bound to the internal `backend` network (`internal: true`), completely isolated from host exposure or public egress.
* **CI/CD Pipeline:** GitHub Actions workflow (`.github/workflows/ci.yml`) featuring Trivy container security scanning and self-hosted integration testing on port `8090`.

---

## Quick Start & Lifecycle Commands

### 1. Setup & Environment Sourcing
The application services directly source environment configuration from `.env` (copied from `.env.example`).

```bash
# Prepare environment configuration
cp .env.example .env

# Build container images using the unprivileged app user (UID 10001)
docker compose build

# Start all containers in detached mode
docker compose up -d

# Verify live container health and status across all 6 services
docker compose ps

```

### 2. Live Verification & Stack Validation

```bash
# Verify stack readiness endpoint via NGINX proxy on port 8090
curl -s [http://127.0.0.1:8090/ready](http://127.0.0.1:8090/ready)

# Verify round-robin routing across app-01, app-02, and app-03
for i in {1..6}; do curl -s [http://127.0.0.1:8090/instance](http://127.0.0.1:8090/instance); done

# Verify persistent records endpoint
curl -s [http://127.0.0.1:8090/records](http://127.0.0.1:8090/records)

# Execute the automated Python test suite to validate end-to-end functionality
python3 validate.py

```

### 3. High Availability & Failover Testing

```bash
# Execute HA failure simulation suite (stops app-01, verifies 100% failover to app-02/app-03, and restores app-01)
python3 failure_test.py

```

### 4. Database Backup, Restore & Persistence Test

```bash
# 1. Insert a test record via NGINX API on port 8090
curl -s -X POST [http://127.0.0.1:8090/records](http://127.0.0.1:8090/records) \
  -H "Content-Type: application/json" \
  -d '{"title": "persistence-test", "value": "survives-recreation"}'

# 2. Run automated database backup script
./backup.sh

# 3. Simulate container recreation (maintaining persistent named volumes)
docker compose up -d --force-recreate

# 4. Confirm record survival in PostgreSQL
curl -s [http://127.0.0.1:8090/records](http://127.0.0.1:8090/records)

# 5. Execute restore test if needed
./restore.sh

```

### 5. Cleanup & Teardown

```bash
# Complete teardown (removes containers, networks, and persistent named volumes)
docker compose down -v

```

---

## CI/CD Workflow Lifecycle

The GitHub Actions pipeline (`.github/workflows/ci.yml`) executes a two-stage hybrid workflow designed to enforce security compliance and validate stack health:

```
[ Git Push / PR to main ]
          │
          ├──► Job 1: security-scan (ubuntu-latest)
          │    ├── Checkout Repository
          │    ├── Set up Docker Buildx
          │    ├── Run Trivy Container Security Vulnerability Scan
          │    ├── Export Scan Results to trivy-report.txt
          │    └── Upload Artifact: trivy-vulnerability-report
          │
          └──► Job 2: validate-stack (self-hosted runner)
               ├── Environment Sourcing (.env / .env.example)
               ├── Orchestrate Docker Compose Stack (docker compose up -d)
               ├── Wait & Poll Readiness Endpoint ([http://127.0.0.1:8090/ready](http://127.0.0.1:8090/ready))
               ├── Execute Automated Integration Tests (python3 validate.py)
               └── Teardown Stack Environment (docker compose down -v)

```

1. **Trigger Phase:** Fires automatically on any `push` or `pull_request` targeting the `main` branch.
2. **Security Scanning Stage (`security-scan`):**
* Executed on a GitHub-managed `ubuntu-latest` runner.
* Runs **Trivy** static analysis to detect `HIGH` and `CRITICAL` vulnerability CVEs.
* Generates `trivy-report.txt` and publishes it as an accessible GitHub Actions **Pipeline Artifact** (`trivy-vulnerability-report`).


3. **Stack Orchestration & Validation Stage (`validate-stack`):**
* Executed on the `self-hosted` runner.
* Ensures `.env` configuration, spins up the 6-service architecture (NGINX, `app-01`, `app-02`, `app-03`, PostgreSQL, Redis), and polls `http://127.0.0.1:8090/ready`.
* Executes `python3 validate.py` to assert end-to-end routing, database persistence, and proxy failover functionality on port `8090`.
* Automatically executes `docker compose down -v` upon completion to maintain a clean runner state.



---

## Video Challenge & Live Fault Diagnosis

During the live video demonstration, executing `./video_challenge.sh` injected a runtime fault and enforced network isolation:

* **Injected Runtime Fault:** Port ingress was reset to `8080`, `app-03` was dropped from the active runtime pool, and strict network isolation was required.
* **Diagnosis:** Inspected running state via `docker compose ps` and `docker compose logs`. NGINX logs confirmed traffic routing only to `app-01` and `app-02`, and database services required strict `internal: true` backend network isolation.
* **Live Repair (Without Teardown):**
1. Configured `docker-compose.yml` to set `networks.backend.internal: true`.
2. Updated NGINX host ingress mapping to port `8090` using `${PUBLIC_PORT:-8090}`.
3. Added `app-03` to `docker-compose.yml` and `nginx/nginx.conf` upstream block.
4. Executed `docker compose up -d app-03 nginx` to apply updates without full-stack resets.



---

## Technical Questions & Answers

### 1. What failed first? What proved the cause? Which failed attempt taught you something?

* **First Failure:** Initial calls to `http://127.0.0.1:8080/ready` returned HTTP `502 Bad Gateway`.
* **Proof:** NGINX error logs showed upstream requests failing against target port `8081` because application backend instances listen internally on port `8080`.
* **Lesson Learned:** Resolving NGINX ports exposed a secondary HTTP `503` failure because the Flask backend logged `OperationalError` when trying to connect to PostgreSQL on `5433` and Redis on `6380`. This taught us that host port mappings used for local development differ from internal container bridge network ports (`5432` and `6379`).

### 2. What patterns did the logs reveal? How did you avoid double-counting requests?

* **Log Patterns:** When backend dependencies were unreachable, NGINX logged retries across upstreams up to `max_fails=2` before returning HTTP `502`. Backend instances logged structured JSON entries containing `event: "dependency_error"`.
* **Deduplication Strategy:** Each request includes a unique `request_id` (UUID). When NGINX retries a request across `app-01`, `app-02`, and `app-03`, all backend instances log entries sharing the exact same `request_id`. Filtering and counting unique `request_id` values prevented double-counting retried client calls.

### 3. How do requests flow? Why these ports, networks, and readiness checks?

* **Request Flow:** Client $\rightarrow$ Host Port `8090` $\rightarrow$ NGINX Proxy (`frontend` network) $\rightarrow$ `app-01` / `app-02` / `app-03` (`8080`) $\rightarrow$ Isolated `backend` network (`internal: true`) $\rightarrow$ PostgreSQL (`5432`) & Redis (`6379`).
* **Ports & Networks:** Host port `8090` is published for public proxy ingress. The `backend` network sets `internal: true` to prevent host port binding or external network access to database and cache layers.
* **Readiness Checks:** The `/ready` endpoint verifies live database and Redis socket connectivity before acknowledging that the container instance is ready to accept production load.

### 4. Why these timeouts, retries, restart settings, and resource limits?

* **Proxy Retries:** NGINX uses `proxy_next_upstream error timeout http_502 http_503` with a `2s` timeout and `max_fails=2` to seamlessly reroute requests to a healthy application instance if a container drops during operation.
* **Restart Settings:** Containers use explicit restart policies (`restart: unless-stopped`) in production, but `restart: "no"` during automated testing so runtime failures break fast in CI testing rather than hanging in infinite restart loops.

### 5. When should validation fail? What does green CI prove, or not prove?

* **Validation Failure:** Occurs when `/ready` returns HTTP 502/503, container health checks fail, database connectivity drops, or `python3 validate.py` assertions fail.
* **What Green CI Proves:** Confirms image security compliance (zero High/Critical Trivy vulnerabilities), Compose configuration validity, successful container startup, dynamic readiness probe matching, and internal database/cache connectivity on target host infrastructure on port `8090`.
* **Trivy Vulnerability Report:** The Trivy container security scan results are generated during the `security-scan` job on `ubuntu-latest` and automatically exported and uploaded as a downloadable artifact (`trivy-vulnerability-report`) in the GitHub Actions run summary.
* **What Green CI Does Not Prove:** Does not guarantee zero latent application bugs under extreme multi-region traffic spikes or physical infrastructure hardware outages.

### 6. Which single points of failure remain? How would you fix them in production?

* **Remaining SPOFs:** Single NGINX edge container and single PostgreSQL database instance.
* **Production Solution:** Deploy multiple NGINX instances behind a Cloud Load Balancer (AWS ALB) and migrate PostgreSQL to a multi-AZ managed database cluster (AWS RDS) with read replicas and automated WAL backups.

### 7. What would you improve? How did you verify AI-assisted work?

* **Improvements:** Implement dynamic secret management via HashiCorp Vault or AWS Secrets Manager, implement SSL/TLS termination on NGINX, and transition to Kubernetes with Horizontal Pod Autoscaling (HPA).
* **Verification of AI Work:** All proposed YAML and code edits were manually tested locally with `docker compose up -d`, verified via `curl -s http://127.0.0.1:8090/ready`, verified for round-robin load distribution across 3 instances, and validated end-to-end on a self-hosted GitHub Actions runner.

---

## Final Submission Evidence Index

| Requirement / Task | Action & Terminal Verification | Commit Reference | Video Timestamp |
| :--- | :--- | :--- | :--- |
| **Repository Baseline & Clean Git State** | Verified clean git tree (`git status`) and commit parity between local and remote `main`. | `47bf6ba` | `00:18` |
| **Container Startup & Service Health** | Built and started containers (`docker compose up -d`), verifying healthy status. | `47bf6ba` | `00:58` |
| **Core Endpoints Verification** | Queried `/` (welcome), `/health` (liveness), and `/ready` (DB & Cache readiness). | `47bf6ba` | `01:10`[cite: 2] |
| **Redis Counter Verification** | Queried `/counter` to confirm active Redis increment caching. | `47bf6ba` | `02:02`[cite: 2] |
| **Round-Robin Load Balancing (2 Backends)** | Tested `/instance` across `app-01` and `app-02` via NGINX proxy. | `47bf6ba` | `02:30`[cite: 2] |
| **Failover & Recovery Demonstration** | Stopped `app-01`, proved zero-downtime routing to `app-02`, and restored `app-01`. | `47bf6ba` | `02:44`[cite: 2] |
| **Historical Log Analysis Demonstration** | Inspected NGINX logs (`docker compose logs nginx`) showing upstream 502/failover events. | `47bf6ba` | `03:15`[cite: 2] |
| **PostgreSQL Data Persistence Test** | Created record via POST `/records`, recreated containers (`up -d --force-recreate`), and verified record survival. | `47bf6ba` | `04:03`[cite: 2] |
| **Validation & Failure Test Automation** | Executed `python3 validate.py` and `python3 failure_test.py` suites successfully. | `47bf6ba` | `04:48`[cite: 2] |
| **Live Challenge Execution & Fault Fix** | Executed `./video_challenge.sh`, diagnosed paused instance state via `docker compose ps`, and fixed live (`unpause`). | `47bf6ba` | `06:01`[cite: 2] |
| **Port Migration (8080 $\rightarrow$ 8090)** | Updated `.env` and `.env.example` to port `8090` live; proved NGINX listens and responds on `8090`. | `47bf6ba` | `08:33`[cite: 2] |
| **3x Backend Horizontal Scaling** | Scaled stack with `app-03` in `docker-compose.yml` and `nginx/nginx.conf`; verified 3-way round-robin. | `47bf6ba` | `11:02`[cite: 2] |
| **Validation Suite Retest (Port 8090)** | Updated `validate.py` target port to `8090` and ran suite to achieve `ALL CHECKS PASSED`. | `47bf6ba` | `17:10`[cite: 2] |
| **On-Screen Commit & Git Push** | Committed all live edits on camera (`git commit`) and force-pushed (`git push origin main --force`). | `aae03ab` | `18:35`[cite: 2] |
| **CI/CD Pipeline & Security Scan** | Triggered GitHub Actions pipeline; verified Trivy security scan artifact and green `validate-stack` build. | `aae03ab` | `20:15`[cite: 2] |


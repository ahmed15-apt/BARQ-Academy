# BARQ Systems - Multi-Container Infrastructure Assessment & Automation

This repository contains the refactored, secure, and automated multi-container Docker Compose infrastructure stack for the BARQ Systems technical assessment.

---

## Technical Architecture & Request Flow


```

[Client / Host Environment]
│
│ (HTTP GET :8080)
▼
┌───────────────┐
│ NGINX Proxy   │  <-- Bound to 127.0.0.1:8080 (frontend network)
└───────┬───────┘
│
├─── (Round-Robin Proxy :8080) ────► [ app-01 ] (UID 10001)
└─── (Upstream Failover :8080) ───► [ app-02 ] (UID 10001)
│
│ (backend network - internal: true)
▼
┌──────────────────────────────┐
│  PostgreSQL (Port 5432)      │
│  - Named Volume: postgres-data
│  - Trust Authentication      │
├──────────────────────────────┤
│  Redis Cache (Port 6379)     │
└──────────────────────────────┘

```

---

## Quick Start & Lifecycle Commands

### 1. Setup & Environment Sourcing
The application services directly source environment configuration from `.env.example` as the canonical template.
```bash
# Build container images using the unprivileged app user (UID 10001)
docker compose build

# Start all containers in detached mode
docker compose up -d

# Verify live container health and process status
docker compose ps

```

### 2. Testing & Stack Validation

```bash
# Verify stack readiness endpoint directly via NGINX proxy on port 8080
curl -s http://127.0.0.1:8080/ready

# Execute the automated Python test suite to validate end-to-end functionality
python3 validate.py

```

### 3. High Availability Failure Simulation

```bash
# Execute HA failure simulation suite (stops app-01, verifies 100% failover traffic to app-02, and restores app-01)
python3 failure_test.py

```

### 4. Database Backup & Restore

```bash
# Run automated database backup script
./backup.sh

# Run automated database restore script
./restore.sh

```

### 5. Cleanup & Reset

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
               ├── Environment Sourcing (.env.example)
               ├── Orchestrate Docker Compose Stack (docker compose up -d)
               ├── Wait & Poll Readiness Endpoint ([http://127.0.0.1:8080/ready](http://127.0.0.1:8080/ready))
               ├── Execute Automated Integration Tests (python3 validate.py)
               └── Teardown Stack Environment (docker compose down -v)

```

1. **Trigger Phase:** Fires automatically on any `push` or `pull_request` targeting the `main` branch.
2. **Security Scanning Stage (`security-scan`):**
* Executed on a GitHub-managed `ubuntu-latest` runner.
* Runs **Trivy** static analysis to detect `HIGH` and `CRITICAL` vulnerability CVEs.
* Generates `trivy-report.txt` and publishes it as an accessible GitHub Actions **Pipeline Artifact** (`trivy-vulnerability-report`).


3. **Stack Orchestration & Validation Stage (`validate-stack`):**
* Executed locally on the target systemd-managed `self-hosted` runner (`barq-docker-compose`).
* Sources `.env.example`, spins up the full architecture (NGINX, 2x Flask API instances, PostgreSQL, Redis), and polls `http://127.0.0.1:8080/ready`.
* Executes `python3 validate.py` to assert end-to-end routing, database operations, and proxy failover functionality.
* Automatically executes `docker compose down -v` upon completion to clean up ephemeral test environments.



---

## Technical Questions & Answers

### 1. What failed first? What proved the cause? Which failed attempt taught you something?

* **First Failure:** Calls to `http://127.0.0.1:8080/ready` returned HTTP `502 Bad Gateway`.
* **Proof:** NGINX error logs showed upstream requests failing against target port `8081` because application backend instances listen on port `8080`.
* **Lesson Learned:** Resolving NGINX ports exposed a secondary HTTP `503` failure because the Flask backend logged `OperationalError` when trying to connect to PostgreSQL on `5433` and Redis on `6380`. This taught us that host port mappings used for local development differ from internal container bridge network ports (`5432` and `6379`).

### 2. What patterns did the logs reveal? How did you avoid double-counting requests?

* **Log Patterns:** When backend dependencies were unreachable, NGINX logged retries across upstreams up to `max_fails=2` before returning HTTP `502`. Backend instances logged structured JSON entries containing `event: "dependency_error"`.
* **Deduplication Strategy:** Each request includes a unique `request_id` (UUID). When NGINX retries a request across `app-01` and `app-02`, both instances log entries sharing the exact same `request_id`. Filtering and counting unique `request_id` values prevented double-counting retried client calls.

### 3. How do requests flow? Why these ports, networks, and readiness checks?

* **Request Flow:** Client $\rightarrow$ Host Port `8080` $\rightarrow$ NGINX (`frontend` network) $\rightarrow$ `app-01` / `app-02` (`8080`) $\rightarrow$ Isolated `backend` network (`internal: true`) $\rightarrow$ PostgreSQL (`5432`) & Redis (`6379`).
* **Ports & Networks:** Host port `8080` is published for public proxy access. The `backend` network sets `internal: true` to prevent host exposure or external egress on database and cache ports.
* **Readiness Checks:** The `/ready` endpoint verifies live database and Redis socket connectivity before acknowledging that the container is ready to accept production load.

### 4. Why these timeouts, retries, restart settings, and resource limits?

* **Proxy Retries:** NGINX uses `proxy_next_upstream error timeout http_502 http_503` with a `2s` timeout and `max_fails=2` to seamlessly reroute requests to a healthy application instance if a container drops during a deployment.
* **Restart Settings:** Containers use `restart: "no"` in Compose so runtime failures break fast in CI testing rather than hanging in infinite restart loops.

### 5. When should validation fail? What does green CI prove, or not prove?

* **Validation Failure:** Occurs when `/ready` returns HTTP 502/503, container health checks fail, or `python3 validate.py` assertions fail.
* **What Green CI Proves:** Confirms image security compliance (zero High/Critical Trivy vulnerabilities), Compose configuration validity, successful container startup, and internal database/cache connectivity on target host infrastructure.
* **Trivy Vulnerability Report:** The Trivy container security scan results are generated during the `security-scan` job on `ubuntu-latest` and automatically exported and uploaded as a downloadable artifact (`trivy-vulnerability-report`) in the GitHub Actions run summary.
* **What Green CI Does Not Prove:** Does not guarantee zero latent application bugs under high multi-region traffic or physical hardware outage conditions.

### 6. Which single points of failure remain? How would you fix them in production?

* **Remaining SPOFs:** Single NGINX edge container and single PostgreSQL container instance.
* **Production Solution:** Deploy multiple NGINX instances behind an AWS Application Load Balancer (ALB) and migrate PostgreSQL to a multi-AZ cluster (AWS RDS) with automated WAL archiving and snapshots.

### 7. What would you improve? How did you verify AI-assisted work?

* **Improvements:** Implement dynamic secret management via HashiCorp Vault or AWS Secrets Manager and transition to Kubernetes with Horizontal Pod Autoscaling (HPA).
* **Verification of AI Work:** All proposed YAML and code edits were manually tested locally with `docker compose up -d`, verified via `curl -s http://127.0.0.1:8080/ready`, and validated end-to-end on a systemd-managed self-hosted GitHub Actions runner.



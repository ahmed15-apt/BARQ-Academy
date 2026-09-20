# Technical Decisions

Record of key architectural decisions made during the infrastructure assessment.

## Decision 1: Unprivileged Runtime Execution Context
- **Choice:** Modified `Dockerfile` to create non-root user `app` (UID 10001) and executed process via `USER app`.
- **Why:** Running container processes as `root` presents severe runtime security risks if container escape bugs occur.
- **Alternative:** Running as default `root` user or mounting docker socket.
- **Trade-off:** Requires explicit ownership assignment (`chown -R app:app`) during build phase.
- **Evidence / commit:** Commit `9b3031c` (`security: update Dockerfile to execute container as non-root app user`).
- **Production improvement:** Combine with read-only root filesystems (`read_only: true`) and dropped Linux capabilities (`cap_drop: [ALL]`).

## Decision 2: PostgreSQL Data Volume Persistence
- **Choice:** Switched PostgreSQL storage volume from volatile `tmpfs` mapping to named volume (`postgres-data:/var/lib/postgresql/data`).
- **Why:** `tmpfs` stores data in memory, causing total database wipe upon container restarts.
- **Alternative:** Host directory bind mount or cloud-managed database (RDS).
- **Trade-off:** Requires manual volume cleanup management (`docker volume rm`) during testing reset cycles.
- **Evidence / commit:** Commit `d01f13a` (`fix(compose): resolve app binding, instance IDs, healthchecks, and db persistence`).
- **Production improvement:** Implement automated snapshot backups and store database volume on managed network block storage (EBS/Ceph).

## Decision 3: Upstream Reverse Proxy Port Synchronization
- **Choice:** Corrected NGINX upstream backend targets from port `8081` to `8080`.
- **Why:** The application backend listens on port `8080`, causing `502 Bad Gateway` errors when proxied to port `8081`.
- **Alternative:** Changing `APP_PORT` inside backend application code.
- **Trade-off:** Minimal; aligning network configuration keeps application defaults intact.
- **Evidence / commit:** Commit `8ed3c37` (`fix(nginx): correct upstream port to 8080, adjust timeouts, and enable proxy retries`).
- **Production improvement:** Implement automated service discovery (e.g., Consul or Kubernetes Service DNS) to eliminate static upstream IP/port mappings.

## Decision 4: High Availability Failover & Upstream Retries
- **Choice:** Configured NGINX `proxy_next_upstream error timeout http_502 http_503` with 2s timeouts and `max_fails=2`.
- **Why:** Ensures client requests are seamlessly rerouted to a backup application instance if one container fails or drops during deployment.
- **Alternative:** Fail fast with immediate error page.
- **Trade-off:** Slightly increased latency during instance failure events while retrying upstreams.
- **Evidence / commit:** Commit `8ed3c37` (`fix(nginx): correct upstream port to 8080, adjust timeouts, and enable proxy retries`).
- **Production improvement:** Add active background NGINX health checks (`zone` directives) to proactively exclude dead backends before client requests arrive.

## Decision 5: Non-Hardcoded Environment Variable Sourcing & Internal Trust Authentication
- **Choice:** Configured `docker-compose.yml` to source environment variables directly from `.env.example` as the canonical template, added `config/app.env` and `.env` to `.gitignore`, and set `POSTGRES_HOST_AUTH_METHOD=trust`.
- **Why:** Prevents secret leakage in version control while eliminating broken local/CI environment setups. Setting `trust` mode allows seamless inter-container connectivity without hardcoded database passwords, secured strictly by Docker's isolated `backend` bridge network (`internal: true`) which blocks external host exposure.
- **Alternative:** Storing plaintext passwords inside tracked environment files, `docker-compose.yml`, or `.env.example`.
- **Trade-off:** Relies on Docker network boundary isolation rather than database password authentication between application and database containers.
- **Evidence / commit:** Commit `docs(env): set .env.example as single source of truth and ignore config/app.env`.
- **Production improvement:** Transition to dynamic secret injection using HashiCorp Vault or AWS Secrets Manager with automated secret rotation.

## Decision 6: Hybrid CI Pipeline, Trivy Artifacts & Self-Hosted Service Deployment
- **Choice:** Configured `.github/workflows/ci.yml` as a two-job pipeline:
  1. **`security-scan`**: Runs container image vulnerability scans (Trivy) on `ubuntu-latest`, exports the report to `trivy-report.txt`, and uploads `trivy-vulnerability-report` as a downloadable GitHub artifact.
  2. **`validate-stack`**: Executes stack build, startup, readiness wait polling, and `python3 validate.py` on a local `self-hosted` runner (`barq-docker-compose`).
- **Runner Deployment:** Deployed the GitHub Actions runner binary on the target host and registered it as a persistent systemd service via `./svc.sh install` and `./svc.sh start` to ensure automatic startup and background execution across host reboots.
- **Why:** Isolates security scanning and artifact publishing on cloud runners while validating actual Docker Compose orchestration, network bindings, and persistent volumes directly on target host infrastructure.
- **Alternative:** Running all jobs on `ubuntu-latest` (lacks local host network fidelity) or running raw ephemeral runner commands (`./run.sh`) without service management.
- **Trade-off:** Requires maintaining the host environment and monitoring the background runner service.
- **Evidence / commit:** Commit `ci(pipeline): enable ubuntu-latest security scan with Trivy artifact and self-hosted deployment`.
- **Production improvement:** Implement runner auto-scaling (e.g., Actions Runner Controller on Kubernetes) to dynamically provision ephemeral runner pods per job.

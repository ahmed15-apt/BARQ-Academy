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

## Decision 5: Non-Hardcoded Credential Ingestion
- **Choice:** Centralized database credentials and passwords inside `config/app.env` and passed them via Compose `env_file`.
- **Why:** Prevents secret leakage in version control while making environment parameters easily configurable.
- **Alternative:** Standard environment variables inside `docker-compose.yml` or Docker Secrets.
- **Trade-off:** Secrets remain readable in standard container environment variables unless using file-based secrets.
- **Evidence / commit:** Commit `d01f13a` (`fix(compose): resolve app binding, instance IDs, healthchecks, and db persistence`).
- **Production improvement:** Transition to dynamic secret injection using HashiCorp Vault or AWS Secrets Manager with secret rotation.

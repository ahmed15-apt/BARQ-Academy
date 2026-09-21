# BARQ Systems - Infrastructure Assessment Evidence Index

This document maps all rubric deliverables and mandatory assessment requirements to their corresponding file/output locations, GitHub commit hashes, and timestamps in the final demonstration video.

---

## Deliverables & Technical Compliance Matrix

| Requirement / Deliverable | File or Command Location | Target Artifact / Output | Commit Hash | Video Timestamp |
| :--- | :--- | :--- | :--- | :--- |
| **Unprivileged Execution** | `Dockerfile` | Container process runs as non-root user `app` (UID `10001`) | `<YOUR_COMMIT_HASH>` | `00:15` |
| **Three-Instance Architecture** | `docker-compose.yml`<br>`nginx/nginx.conf` | 3 app instances (`app-01`, `app-02`, `app-03`) balanced behind NGINX | `<YOUR_COMMIT_HASH>` | `00:40` |
| **NGINX Health Check** | `docker-compose.yml` | Healthcheck block added under `nginx` (`wget -q --spider http://127.0.0.1/ready`) | `<YOUR_COMMIT_HASH>` | `00:55` |
| **Host Port Binding (8090)** | `docker-compose.yml`<br>`nginx/nginx.conf` | Host port `8090` bound to NGINX edge container (`127.0.0.1:8090:80`) | `<YOUR_COMMIT_HASH>` | `01:15` |
| **Readiness Endpoint** | `curl -s http://127.0.0.1:8090/ready` | Returns HTTP 200 `{"status":"ready"}` verifying DB & Redis health | `<YOUR_COMMIT_HASH>` | `01:35` |
| **Recorded Challenge Receipt** | `.assessment/challenge.json` | Generated single-run proof output from running `./video_challenge.sh` | `<YOUR_COMMIT_HASH>` | `01:55` |
| **High Availability Failover** | `failure_test.py` | Validates 100% request success rate during backend container outage & recovery | `<YOUR_COMMIT_HASH>` | `02:20` |
| **Database Backup Execution** | `backup.sh` | Exports PostgreSQL dump from persistent volume to local snapshot file | `<YOUR_COMMIT_HASH>` | `02:45` |
| **Database Restore Execution** | `restore.sh` | Restores database state into PostgreSQL from backup snapshot file | `<YOUR_COMMIT_HASH>` | `03:00` |
| **Storage Persistence** | `docker-compose.yml` | Named volume `postgres-data` preserves state across container restarts | `<YOUR_COMMIT_HASH>` | `03:20` |
| **Trivy Vulnerability Artifact** | `.github/workflows/ci.yml` | `trivy-report.txt` uploaded as downloadable GitHub Actions pipeline artifact | `<YOUR_COMMIT_HASH>` | `03:40` |

---

## Deliverable Documentation Mapping

* **Architecture Diagram:** Available in [`architecture.png`](../architecture.png).
* **NGINX Service Health:** Health check integrated into [`docker-compose.yml`](../docker-compose.yml) under the `nginx` service block to meet `(healthy)` preflight status requirements.
* **Security & Risk Review:** Comprehensive domain analysis available in [`security_review.md`](../security_review.md).
* **Architectural Decisions:** Decision log available in [`decisions.md`](../decisions.md).
* **AI Disclosure:** Usage and verification logs available in [`AI_USAGE.md`](../AI_USAGE.md).

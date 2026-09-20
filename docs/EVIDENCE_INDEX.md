# BARQ Systems - Infrastructure Assessment Evidence Index

This document maps all rubric deliverables and mandatory assessment requirements to their corresponding file/output locations, GitHub commit hashes, and timestamps in the final demonstration video.

---

## Deliverables & Technical Compliance Matrix

| Requirement / Deliverable | File or Command Location | Target Artifact / Output | Commit Hash | Video Timestamp |
| :--- | :--- | :--- | :--- | :--- |
| **Unprivileged Execution** | `Dockerfile` | Container process runs as non-root user `app` (UID `10001`) | `<commit_hash>` | `00:15` |
| **Three-Instance Architecture** | `docker-compose.yml`<br>`nginx/nginx.conf` | 3 app instances (`app-01`, `app-02`, `app-03`) balanced behind NGINX | `<commit_hash>` | `00:40` |
| **Host Port Binding (8090)** | `docker-compose.yml`<br>`nginx/nginx.conf` | Host port `8090` bound to NGINX edge container (`127.0.0.1:8090:80`) | `<commit_hash>` | `01:05` |
| **Readiness Endpoint** | `curl -s http://127.0.0.1:8090/ready` | Returns HTTP 200 `{"status":"ready"}` verifying DB & Redis health | `<commit_hash>` | `01:25` |
| **Recorded Challenge Receipt** | `.assessment/challenge.json` | Generated single-run proof output from running `./video_challenge.sh` | `<commit_hash>` | `01:45` |
| **High Availability Failover** | `failure_test.py` | Validates 100% request success rate during backend container outage & recovery | `<commit_hash>` | `02:10` |
| **Database Backup Execution** | `backup.sh` | Exports PostgreSQL dump from persistent volume to local snapshot file | `<commit_hash>` | `02:35` |
| **Database Restore Execution** | `restore.sh` | Restores database state into PostgreSQL from backup snapshot file | `<commit_hash>` | `02:50` |
| **Storage Persistence** | `docker-compose.yml` | Named volume `postgres-data` preserves state across container restarts | `<commit_hash>` | `03:10` |
| **Trivy Vulnerability Artifact** | `.github/workflows/ci.yml` | `trivy-report.txt` uploaded as downloadable GitHub Actions pipeline artifact | `<commit_hash>` | `03:30` |

---

## Deliverable Documentation Mapping

* **Architecture Diagram:** Available in [`architecture.mmd`](../architecture.mmd) and [`architecture.png`](../architecture.png).
* **Security & Risk Review:** Comprehensive domain analysis available in [`security_review.md`](../security_review.md).
* **Architectural Decisions:** Decision log available in [`decisions.md`](../decisions.md).
* **AI Disclosure:** Usage and verification logs available in [`AI_USAGE.md`](../AI_USAGE.md).

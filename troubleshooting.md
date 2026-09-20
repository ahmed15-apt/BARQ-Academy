# Troubleshooting journal

Keep chronological entries. Copy this block for each meaningful investigation.

## Entry / date / time
- Symptom:
- Hypothesis:
- Command or test:
- Actual output:
- Failed attempt and what changed your thinking:
- Root cause:
- Fix:
- Retest evidence:
- Related commit:
- Remaining uncertainty:

Do not fabricate a failed attempt just to fill the template. Record actual attempts.
---

## Entry 1 / 2026-08-20 / Root Cause Investigation
- **Symptom:** System returned intermittent HTTP 502, 503, and 504 errors across multiple endpoints.
- **Hypothesis:** Failures are caused by a combination of application crashes, database credential errors, cache timeouts, and proxy timeout settings.
- **Command or test:**
  - `wc -l logs/*.log`
  - `grep -o '"status":[^,]*' logs/access.log | sort | uniq -c | sort -nr`
  - `grep -i "error" logs/error.log`
  - `grep -E "ERROR|WARN" logs/application.log`
  - `grep "lab-000122" logs/access.log` (command used to isolate specific request ID logs across files)
- **Actual output:**
  - `grep -o '"status":[^,]*' logs/access.log | sort | uniq -c | sort -nr` extracted the status codes from JSON logs accurately: 200, 404, 502, 503, and 504.
  - NGINX `error.log`: `connect() failed (111: Connection refused)` for `172.23.0.12:8080`.
  - NGINX `error.log`: `upstream timed out (110: Operation timed out)` on `/records`.
  - Application `application.log`: `dependency_error` on `redis` (`TimeoutError`) and `postgres` (`InvalidPassword`).
- **Failed attempt and what changed your thinking:** Standard space-delimited `awk` commands failed to parse `access.log` status codes because the file is JSON-formatted. Running `grep -o '"status":[^,]*' logs/access.log | sort | uniq -c | sort -nr` extracted the exact status code distributions. Additionally, isolating specific log entries by request ID (e.g., `grep "lab-000122"`) linked specific client requests directly to NGINX proxy errors and application exceptions.
- **Root Cause:**
  1. `app-02` instance was down (Connection refused -> 502).
  2. Redis cache timed out after 2000ms -> 503.
  3. PostgreSQL rejected connection due to invalid password -> 503.
  4. Query execution (~2700ms) exceeded NGINX's 2000ms proxy read timeout -> 504.
- **Fix:** Documented exact failure parameters in `log_analysis.md` and recorded investigation steps to inform Part 2 Docker Compose environment configuration.
- **Retest evidence:** Correlated `request_id` values (`lab-000122`, `lab-000292`, `lab-000484`, `lab-000606`) across all three log files using targeted `grep` commands.
- **Related commit:** Baseline documentation commit.
- **Remaining uncertainty:** Service container configuration needs alignment in `docker-compose.yml` and `config/app.env`.

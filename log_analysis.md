# Log Analysis & Evidence Correlator

## Template Answers & Evidence Summary

### 1. What patterns did the logs reveal?
- **NGINX Reverse Proxy:** Logged upstream requests showing status `503` when backends were unreachable, retrying upstream up to `max_fails=2` before returning HTTP `502 Bad Gateway` to clients.
- **Application Backend (`app-01` / `app-02`):** Output structured JSON logs containing `event: "dependency_error"`, identifying specific failed drivers (`dependency: "postgres"`, `dependency: "redis"`).
- **PostgreSQL:** Recorded `LOG: database system is ready to accept connections` after volume initialization.

### 2. How did you avoid double-counting requests?
- **Request Tracing via Correlation ID:** Evaluated HTTP requests using the `request_id` field (e.g., `request_id: "0220566d9bee02078c866ae1bfe9d77e"`).
- **Deduplication Strategy:** When NGINX retried a failed upstream request across `app-01` and `app-02`, both app instances logged HTTP 503 entries containing the *exact same* `request_id`. Counting unique `request_id` values rather than raw log lines prevented double-counting retried client requests.

---

## Log Correlation Matrix

| Timestamp | Service | Log Event / Message | Correlated Meaning |
| :--- | :--- | :--- | :--- |
| `11:55:17` | `postgres` | `database system is ready to accept connections` | DB container finished boot process. |
| `11:55:20` | `nginx` | `"upstream_status": "503, 503"` | Proxy attempted both upstreams, received 503 from dependencies. |
| `11:55:20` | `app-02` | `"dependency_error", "dependency": "postgres"` | App failed to reach DB due to port/credential mismatch. |
| `11:55:32` | `nginx` | `no live upstreams while connecting to upstream` | NGINX temporarily marked upstreams down after max fails. |

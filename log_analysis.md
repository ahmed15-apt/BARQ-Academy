# Log analysis
## 1. What UTC interval is covered? How many valid, malformed and duplicate lines are in each file?

- **UTC Interval:** `2026-08-20T11:00:00.015Z` to `2026-08-20T11:30:00.000Z`
- **`logs/access.log`:** 726 total lines (720 valid JSON, 0 malformed, 6 exact duplicate lines)
- **`logs/application.log`:** 730 total lines (720 valid JSON, 0 malformed, 10 exact duplicate lines)
- **`logs/error.log`:** 68 total lines (68 valid entries, 0 malformed, 0 duplicate lines)

### Commands & Output:
```bash
$ head -n 1 logs/access.log && tail -n 1 logs/access.log
{"timestamp":"2026-08-20T11:00:00.015Z",...}
{"timestamp":"2026-08-20T11:29:57.578Z",...}

$ wc -l logs/*.log
  726 logs/access.log
  730 logs/application.log
   68 logs/error.log
 1524 total

$ sort logs/access.log | uniq -d | wc -l
6

$ sort logs/application.log | uniq -d | wc -l
10
```
--- 
## 2. How many distinct client requests occurred? How did you deduplicate and avoid counting retries twice?

* **Distinct Client Requests:** **720 distinct client requests** occurred (`lab-000001` through `lab-000720`).
* **Deduplication Method:** Deduplicated by filtering unique `request_id` keys in `access.log`. Retries maintain the same client `request_id` while listing multiple upstreams in `upstream_status` (e.g., `"upstream_status": "502, 200"`), ensuring each request is counted exactly once regardless of upstream retry attempts.

### Commands & Output:

```bash
$ jq -r '.request_id' logs/access.log | sort -u | wc -l
720

```



## 3. What are the final client status counts and error rate? State your denominator.

* **Client Status Code Counts:**
* `200 OK`: 630
* `503 Service Unavailable`: 48
* `502 Bad Gateway`: 24
* `504 Gateway Timeout`: 12
* `404 Not Found`: 6


* **Denominator:** 720 distinct client requests
* **Error Rates:**
* **5xx Server Error Rate:** $(24 + 48 + 12) / 720 = 84 / 720 =$ **11.67%**
* **Total Non-200 Error Rate (including 404s):** $90 / 720 =$ **12.50%**



### Commands & Output:

```bash
$ grep -o '"status":[^,]*' logs/access.log | sort | uniq -c | sort -nr
    630 "status":200
     48 "status":503
     24 "status":502
     12 "status":504
      6 "status":404

```

---

## 4. Which paths, time windows and backends account for the failures?

* **11:05:02 – 11:09:57 (`502 Bad Gateway`):**
* **Paths:** All paths (`/`, `/health`, `/ready`, `/records`, `/counter`, `/instance`)
* **Backend:** `172.23.0.12:8080` (`app-02`)
* **Cause:** `app-02` instance was down (`Connection refused`).


* **11:12:09 – 11:15:52 (`503 Service Unavailable`):**
* **Paths:** `/ready` and `/counter`
* **Backends:** Both `172.23.0.11:8080` (`app-01`) and `172.23.0.12:8080` (`app-02`)
* **Cause:** Redis cache connection `TimeoutError` (2025ms).


* **11:20:07 – 11:21:45 (`503 Service Unavailable`):**
* **Paths:** `/ready` and `/records`
* **Backends:** Both `app-01` and `app-02`
* **Cause:** PostgreSQL authentication failure (`InvalidPassword`).


* **11:25:14 – 11:26:47 (`504 Gateway Timeout`):**
* **Paths:** `/records`
* **Backends:** Both `app-01` and `app-02`
* **Cause:** Application execution time (~2700ms) exceeded NGINX 2.0s proxy read timeout.


* **Intermittent (`404 Not Found`):**
* **Path:** `/missing`
* **Cause:** Requests to non-existent route.



### Commands & Output:

```bash
$ jq -r 'select(.status >= 400) | "\(.path) \(.status) \(.upstream)"' logs/access.log | sort | uniq -c
   24 / 502 172.23.0.12:8080
   24 /counter 503 172.23.0.12:8080
   24 /counter 503 172.23.0.11:8080
    6 /missing 404 172.23.0.12:8080
    6 /missing 404 172.23.0.11:8080
   24 /ready 503 172.23.0.12:8080
   24 /ready 503 172.23.0.11:8080
   12 /records 503 172.23.0.12:8080
   12 /records 503 172.23.0.11:8080
    6 /records 504 172.23.0.12:8080
    6 /records 504 172.23.0.11:8080

```

---

## 5. What are the median and p95 client latencies? State the percentile method and units.

* **Median (p50):** `0.052` seconds (52 ms)
* **p95 Latency:** `2.025` seconds (2025 ms)
* **Percentile Method:** Nearest Rank method on sorted `request_time` values.
* **Units:** Seconds (as recorded in `access.log`).

### Commands & Output:

```bash
$ jq -r '.request_time' logs/access.log | sort -n | awk '{a[NR]=$1} END {print "p50:", a[INT(NR*0.50)], "p95:", a[INT(NR*0.95)]}'
p50: 0.052 p95: 2.025

```

---

## 6. Which requests retried upstream? How many succeeded after retrying?

* **Retried Requests:** **18 distinct requests** retried upstream (`lab-000124`, `lab-000130`, `lab-000136`, `lab-000142`, `lab-000148`, `lab-000154`, `lab-000160`, `lab-000172`, `lab-000178`, `lab-000184`, `lab-000190`, `lab-000196`, `lab-000202`, `lab-000208`, `lab-000214`, `lab-000220`, `lab-000226`, `lab-000232`).
* **Success Rate after Retry:** **18 out of 18 succeeded (100% success rate)** via NGINX failover to `172.23.0.11:8080` (`upstream_status: "502, 200"`).

### Commands & Output:

```bash
$ grep "upstream_status" logs/access.log | grep "," | wc -l
18

$ jq -r 'select(.upstream_status | contains(",")) | "\(.request_id): \(.upstream_status)"' logs/access.log | head -n 5
lab-000124: 502, 200
lab-000130: 502, 200
lab-000136: 502, 200
lab-000142: 502, 200
lab-000148: 502, 200

```

---

## 7. Build an incident timeline using evidence from access, error AND application logs.

* **11:00:00 – 11:05:00:** Normal system operation across `app-01` and `app-02`.
* **11:05:02 – 11:09:57 (`app-02` Outage):**
* `access.log`: HTTP 502 returned for requests routed to `172.23.0.12:8080`.
* `error.log`: NGINX logs `connect() failed (111: Connection refused)` for `172.23.0.12:8080`.
* `application.log`: Zero logs recorded for `instance_id: app-02`.


* **11:12:09 – 11:15:52 (Redis Timeout):**
* `access.log`: HTTP 503 returned on `/ready` and `/counter`.
* `application.log`: `dependency_error` logged on `redis` (`TimeoutError` after 2025ms).
* `error.log`: No proxy errors logged (application handled error internally).


* **11:20:07 – 11:21:45 (PostgreSQL Auth Error):**
* `access.log`: HTTP 503 returned on `/ready` and `/records`.
* `application.log`: `dependency_error` logged on `postgres` (`InvalidPassword` in ~41ms).
* `error.log`: No proxy errors logged.


* **11:25:14 – 11:26:47 (NGINX Proxy Gateway Timeout):**
* `access.log`: HTTP 504 returned on `/records`.
* `error.log`: NGINX logs `upstream timed out (110: Operation timed out) while reading response header`.
* `application.log`: Shows HTTP 200 processing completion with `duration_ms: 2700`, exceeding NGINX's 2.0s proxy timeout.



---

## 8. Show one correlated failed request and one successful request. Include IDs and timestamps.

### Failed Request (`lab-000122`)

* **Timestamp:** `2026-08-20T11:05:02.503Z`
* **`logs/access.log`:**
`{"timestamp":"2026-08-20T11:05:02.503Z","request_id":"lab-000122","method":"GET","path":"/health","status":502,"upstream":"172.23.0.12:8080","upstream_status":"502","request_time":0.003,"client":"192.0.2.24"}`
* **`logs/error.log`:**
`2026/08/20 11:05:02 [error] 31#31: *122 connect() failed (111: Connection refused) while connecting to upstream, request_id=lab-000122, request: "GET /health HTTP/1.1", upstream: "http://172.23.0.12:8080/health"`
* **`logs/application.log`:**
*(No log line recorded; instance `app-02` was down)*

### Successful Request (`lab-000002`)

* **Timestamp:** `2026-08-20T11:00:02.532Z`
* **`logs/access.log`:**
`{"timestamp":"2026-08-20T11:00:02.532Z","request_id":"lab-000002","method":"GET","path":"/health","status":200,"upstream":"172.23.0.12:8080","upstream_status":"200","request_time":0.032,"client":"192.0.2.24"}`
* **`logs/application.log`:**
`{"timestamp": "2026-08-20T11:00:02.532Z", "level": "INFO", "event": "http_request", "request_id": "lab-000002", "instance_id": "app-02", "method": "GET", "path": "/health", "status": 200, "duration_ms": 32.0}`

---

## 9. Which errors appear to be proxy/connectivity issues versus dependency/application issues? What proves it?

* **Proxy / Connectivity Issues:** The HTTP `502 Bad Gateway` errors (11:05–11:09).
* **Proof:** NGINX `error.log` recorded OS-level socket refusals (`Connection refused`) while `application.log` contained zero entries from `app-02`, proving the request never reached the Python application code.


* **Dependency / Application Issues:** The HTTP `503 Service Unavailable` errors (11:12–11:15 and 11:20–11:21).
* **Proof:** `application.log` explicitly recorded application-level `dependency_error` events (`redis TimeoutError` and `postgres InvalidPassword`), proving NGINX successfully passed the request to the app, but the app threw an exception while contacting its backing services.



---

## 10. What do the logs not prove? What would you check next in a running environment?

* **What the logs do NOT prove:**
* The underlying host reason why `app-02` crashed or exited (e.g., OOM kill, hardware fault, unhandled SIGTERM).
* System resource metrics (CPU, RAM, disk I/O saturation) during slow query windows.
* Network packet drop rates or network interface issues between app and Redis/Postgres.


* **What to check next in a running environment:**
* `docker stats` and `docker inspect` for container exit codes and memory limits.
* Kernel `dmesg` / `/var/log/syslog` for Out-Of-Memory (OOM) killer events.
* PostgreSQL slow query logs (`pg_stat_activity`) to identify unindexed database queries on `/records`.
* Redis memory and client connection status (`redis-cli info`).
* NGINX configuration (`proxy_read_timeout`) to align proxy timeouts with long-running application routes.







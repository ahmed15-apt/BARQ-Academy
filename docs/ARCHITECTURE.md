# BARQ Systems - System Architecture & Infrastructure Overview

This document describes the 3-instance high-availability architecture for the BARQ Systems infrastructure assessment.

---

## 1. System Overview & Component Layout

The complete system architecture is illustrated in [`architecture.png`](./architecture.png) (and [`architecture.mmd`](./architecture.mmd)).

### Core Components & Port Binding
* **Host Edge Ingress:** `127.0.0.1:8090` mapped directly to the NGINX edge container port `80`.
* **NGINX Edge Proxy (`nginx`):** Acts as the primary entry point inside the `frontend` bridge network, balancing incoming traffic across application instances using a round-robin strategy.
* **Flask Application Instances (`app-01`, `app-02`, `app-03`):** Three identical Python/Flask API containers executing as an unprivileged user (`UID 10001`). Dual-attached to both `frontend` and `backend` networks.
* **Database Storage (`postgres`):** PostgreSQL 16 server isolated on port `5432` within the `backend` network. Persists application state using named volume `postgres-data`.
* **In-Memory Cache (`redis`):** Redis 7 server isolated on port `6379` within the `backend` network for session state and atomic counters.

---

## 2. Request Flow & Health / Readiness Dynamics

1. **Ingress Route:** Client traffic hits `http://127.0.0.1:8090/`.
2. **Reverse Proxy & Load Balancing:** NGINX forwards requests across healthy app instances on internal port `8080`.
3. **Readiness Probe (`/ready`):** Calling `/ready` prompts the responding application instance to verify TCP connectivity and database access against both PostgreSQL and Redis before returning HTTP 200 `{"status":"ready"}`.
4. **Network Security Isolation:** PostgreSQL and Redis do not publish host ports and reside strictly within the isolated `backend` network.

---

## 3. Remaining Single Points of Failure (SPOFs) & Risk Mitigations

As highlighted in **`architecture.png`** (marked with warning icons ⚠️ and red dashed borders), the following Single Points of Failure remain in this single-host Docker Compose deployment:

1. **NGINX Edge Proxy (`nginx`):** 
   * **Risk:** Running a single NGINX container means proxy failure or container restart halts all edge traffic routing.
   * **Mitigation:** Deploy redundant NGINX containers behind an external Cloud Load Balancer (e.g., AWS ALB) or use Virtual IP failover via `keepalived`.

2. **PostgreSQL Database (`postgres`):**
   * **Risk:** A single database container represents a single point of failure for persistent writes and state reads.
   * **Mitigation:** Implement PostgreSQL primary-replica streaming replication with automated failover (e.g., Patroni / PgBouncer).

3. **Redis Cache Engine (`redis`):**
   * **Risk:** Standalone Redis container failure disrupts state counters and caching features.
   * **Mitigation:** Upgrade to a Redis Sentinel setup or a managed Redis Cluster.

4. **Compute Host Node:**
   * **Risk:** All containers reside on a single Docker host machine; host hardware, hypervisor, or OS failure takes down the entire stack.
   * **Mitigation:** Orchestrate containers across multi-AZ worker nodes using Kubernetes (EKS) or Docker Swarm.

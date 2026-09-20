# Security Review & Risk Assessment

## Implemented Security Controls

1. **Unprivileged Execution Context (Container User):**
   - *Risk:* Running containerized processes as `root` risks full host compromise in container-escape scenarios.
   - *Control:* Modified `Dockerfile` to create non-root user `app` (UID 10001) and run via `USER app`.

2. **Network Boundary Isolation (Networks):**
   - *Risk:* Publicly exposed database and cache ports allow direct external brute-force attacks.
   - *Control:* Placed PostgreSQL and Redis on an isolated `backend` bridge network with `internal: true`. Neither port `5432` nor `6379` is published to the host.

3. **Secret Elimination from Source Control (Secrets):**
   - *Risk:* Hardcoded passwords inside Git repositories lead to credential leakage.
   - *Control:* Sourced configuration from `.env.example`, ignored `config/app.env` and `.env` in `.gitignore`, and leveraged `POSTGRES_HOST_AUTH_METHOD=trust` strictly within the internal network.

4. **Automated Static Vulnerability Scanning (Images):**
   - *Risk:* Deploying images with vulnerable dependencies or base OS libraries.
   - *Control:* Integrated Trivy image scanning in GitHub Actions (`security-scan` job) with `HIGH,CRITICAL` severity thresholds and report artifact publishing.

---

## Production Security Improvements & Remaining Risks

5. **Lack of Dynamic Secret Management (Secrets/Vault):**
   - *Risk:* Relying on `trust` authentication within the Docker network lacks cryptographic authorization.
   - *Production Improvement:* Integrate HashiCorp Vault or AWS Secrets Manager to inject short-lived dynamic credentials at container startup.

6. **Host Mount Data Persistence Risks (Backups & Storage):**
   - *Risk:* Data stored in named Docker volumes (`postgres-data`) is vulnerable to host drive corruption or unencrypted storage access.
   - *Production Improvement:* Implement automated database WAL archiving, encrypted EBS/Ceph volume storage, and nightly snapshot restoration tests.

7. **Missing Distributed Tracing & Centralized Audit Logging (Monitoring):**
   - *Risk:* Plaintext stdout logging without centralized log shipping (e.g., ELK/Datadog) hampers incident response and tamper detection.
   - *Production Improvement:* Implement structured JSON log shippers (Fluentbit/Vector) with TLS encryption and tamper-evident audit logging.

8. **Single Point of Failure on Reverse Proxy (Availability & Single Points of Failure):**
   - *Risk:* A single NGINX container instance acts as a SPOF for edge traffic.
   - *Production Improvement:* Deploy redundant NGINX edge instances behind an external Cloud/Hardware Load Balancer (ALB/Keepalived) with active health checking.

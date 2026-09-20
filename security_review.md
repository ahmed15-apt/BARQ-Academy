# Security and production-readiness review

Record at least 8 concrete risks or improvements relevant to your final solution.
This is a review requirement, not the number of hidden faults.

For each finding:
- Risk and evidence:
- Impact:
- Implemented fix / commit:
- Production follow-up:
- How to verify:

Cover secrets, ports, container user, image selection, networks, persistence/backup,
logging/monitoring and availability. Separate completed work from planned improvements.

## Container Execution Privilege
- **Status:** Resolved
- **Change:** Updated `Dockerfile` to switch runtime user from `root` to non-root `app` user (`uid 10001`).
- **Verification:** Built and verified execution context via `docker run --rm <image> whoami` returning `app`.

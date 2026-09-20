# AI Usage Disclosure

## Tools Used
- **AI Assistant:** Gemini (Interactive LLM Collaborator)

## Purpose
- Assisted in refactoring `docker-compose.yml` and `.github/workflows/ci.yml`.
- Helped diagnose internal port mismatches (5433/6380 vs 5432/6379) and upstream 502 Bad Gateway responses.
- Assisted in structuring documentation files (`decisions.md`, `security_review.md`, `troubleshooting.md`).

## Affected Files
- `docker-compose.yml`
- `.env.example`
- `.gitignore`
- `.github/workflows/ci.yml`
- `decisions.md`
- `security_review.md`
- `troubleshooting.md`
- `README.md`

## Human Verification & Testing
- Every configuration change was tested locally using `docker compose up -d` and verified via `curl -s http://127.0.0.1:8080/ready`.
- GitHub Actions pipeline runs were verified end-to-end on a systemd-managed self-hosted runner.
- Security scan outputs from Trivy were reviewed manually to ensure zero high/critical vulnerabilities.

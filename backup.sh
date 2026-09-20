#!/usr/bin/env bash
set -euo pipefail

mkdir -p backups
BACKUP_FILE="backups/db_backup_$(date +%Y%m%d_%H%M%S).sql"

echo "Creating PostgreSQL database backup..."
docker exec postgres pg_dump -U barq_app -d barq_tasks > "$BACKUP_FILE"

echo "Backup created successfully at $BACKUP_FILE"

#!/usr/bin/env bash
set -euo pipefail

LATEST_BACKUP=$(ls -t backups/*.sql 2>/dev/null | head -n 1)

if [ -z "$LATEST_BACKUP" ]; then
  echo "Error: No backup file found in backups/"
  exit 1
fi

echo "Restoring database from $LATEST_BACKUP..."

# Drop existing schema to avoid key conflicts, then restore
docker exec -i postgres psql -U barq_app -d barq_tasks -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker exec -i postgres psql -U barq_app -d barq_tasks < "$LATEST_BACKUP"

echo "Database restored successfully from $LATEST_BACKUP"

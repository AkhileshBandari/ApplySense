#!/bin/bash
# scripts/backup_db.sh

set -e

BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/applysense_db_${TIMESTAMP}.sql"

echo "Backing up ApplySense database..."
docker exec applysense_db pg_dump -U applysense_user applysense > "$BACKUP_FILE"

echo "Backup created successfully: $BACKUP_FILE"

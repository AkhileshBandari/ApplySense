#!/bin/bash
# scripts/restore_db.sh

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/restore_db.sh <backup_file.sql>"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file $BACKUP_FILE does not exist."
    exit 1
fi

echo "Restoring database from $BACKUP_FILE..."

# Terminate existing connections and drop/recreate database safely
docker exec applysense_db psql -U applysense_user -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'applysense';"
docker exec applysense_db psql -U applysense_user -d postgres -c "DROP DATABASE applysense;"
docker exec applysense_db psql -U applysense_user -d postgres -c "CREATE DATABASE applysense;"

echo "Applying backup..."
cat "$BACKUP_FILE" | docker exec -i applysense_db psql -U applysense_user -d applysense

echo "Database restored successfully."

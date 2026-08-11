# PHASE 11 DISASTER RECOVERY

## OVERVIEW
ApplySense architecture localizes persistent truth entirely to the PostgreSQL database instance (`applysense_db`). The Redis broker acts purely as an ephemeral queue and cache. Should catastrophic failure occur, disaster recovery targets restoring PostgreSQL to the last verified snapshot.

## BACKUP PROCEDURE

### Automated Backups
Database backups should be scheduled periodically (e.g. via cron job running `scripts/backup_db.sh`).
```bash
./scripts/backup_db.sh
```
This drops a timestamped SQL snapshot in the `./backups/` directory (e.g., `applysense_db_20260810_120000.sql`).

### Off-Site Backup Replication
Backups must be securely transferred off the host machine (e.g., pushed to AWS S3 / GCP Cloud Storage).

## RECOVERY PROCEDURE

### 1. Hard Crash Pre-requisites
If the server crashed, ensure the base Docker containers are running first.
```bash
docker-compose up -d db
```
Wait for Postgres to accept connections.

### 2. Execution Restoration
```bash
./scripts/restore_db.sh ./backups/applysense_db_20260810_120000.sql
```
The script will safely terminate active backend connections, drop the corrupted `applysense` DB, create a fresh schema block, and apply the snapshot via `cat > docker exec`.

### 3. Worker State Initialization
Because Redis was not restored, all pending tasks in the broker queue are permanently dropped. This is the **correct safety behavior**. 
The Career OS reconciliation engine is designed to regenerate state idempotently.
```bash
# Start the rest of the application
docker-compose up -d
```

### 4. Post-Recovery Diagnostics
- Access the `Ops Dashboard` through the frontend.
- Verify that `CareerOutcomeEvent` metrics align with the backup timestamp.
- Ensure Auto-Apply execution limits for the week did not artificially reset beyond their canonical DB timestamp.

## PARTIAL STATE OR IN-FLIGHT APPLICATION CRASH
If the backend crashes **during** a Playwright session, the job execution will record an `UNKNOWN` execution state in the DB. ApplySense gracefully falls back to `USER_ACTION_REQUIRED` for any `UNKNOWN` tasks preventing silent dual-applications.

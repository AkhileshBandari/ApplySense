# PHASE 11 PRODUCTION RUNBOOK

## OVERVIEW
ApplySense Career OS utilizes a containerized Django + Celery backend with a Vite/React frontend. State relies on PostgreSQL, and queue/broker/caching relies on Redis.

## STANDARD OPERATIONS

### 1. Starting the Application
```bash
docker-compose up -d
```
Starts all dependency containers sequentially, honoring wait dependencies.

### 2. Stopping the Application
```bash
docker-compose down
```
Safely spins down containers. **Does not destroy persistent volumes** (PostgreSQL data safely remains).

### 3. Log Aggregation & Inspection
```bash
docker-compose logs -f backend_web
docker-compose logs -f celery_browser
```
Logs format with `X-Request-ID` correlations for easy cross-service traceability.

### 4. Updating Application Code (Zero-Downtime Strategy)
ApplySense supports rolling restarts for stateless containers (Web + Celery).
1. Pull new codebase.
2. Build new images: `docker-compose build`
3. Spin up new replacements: `docker-compose up -d --no-deps --build backend_web`

### 5. Running Ad-hoc Management Commands
```bash
docker exec -it applysense_backend_web python manage.py shell
```

## AUTO-APPLY EMERGENCY SHUTDOWN (KILL SWITCHES)

In the event of an automated ATS integration leak, abuse, or malfunction, administrators can leverage these tiered kill switches:

**Level 1: System-Wide Execution Pause**
Stops all browser workers from dispatching applications universally.
*Action*: Set `AUTO_APPLY_GLOBAL_ENABLED=False` in backend `.env` and restart worker.

**Level 2: Provider-Specific Pause**
Stops applications targeting a specific ATS vendor experiencing issues.
*Action*: Django Admin -> Providers -> Uncheck `Is Active`.

**Level 3: User-Specific Pause**
Halts automation loops for a single rogue candidate context.
*Action*: Django Admin -> Users -> Disable Auto-Apply Flag.

## INCIDENT RESPONSE PROCEDURES

### 1. Redis Unavailability
**Symptoms**: `/api/health/readiness/` degrades. Celery tasks halt. OS Dashboard renders.
**Action**: 
- Inspect memory usage on Redis container: `docker stats applysense_redis`.
- Flush if required (cache only): `docker exec -it applysense_redis redis-cli FLUSHALL`.
- Restart container: `docker restart applysense_redis`.

### 2. PostgreSQL Unavailability
**Symptoms**: `/api/health/liveness/` degrades. Application yields 500 errors.
**Action**:
- Check for connection pool exhaustion.
- Execute Disaster Recovery (DB Restore) if corruption detected.

### 3. Chromium Headless Worker Crash
**Symptoms**: Playwright timeout exceptions log repeatedly. `shm` exhaustion.
**Action**:
- Browser workers isolate failures safely. The automation flow degrades to `USER_ACTION_REQUIRED`.
- Verify `shm_size: 2gb` in `docker-compose.yml`. Restart celery_browser container.

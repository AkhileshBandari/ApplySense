# Auto Apply Disaster Recovery Plan

## Incident Categories

### 1. Redis Failure / Data Loss
- **Impact**: Loss of queued Celery tasks and active scheduler states.
- **Recovery**: The system is designed to be idempotent. `AutoApplyRun` states are tracked in PostgreSQL. If tasks in Redis are lost:
  1. Restart Redis.
  2. The `schedule_auto_apply_runs` beat task will automatically sweep the database for users whose rules dictate an application run should happen and who don't have an active run, queuing them again.

### 2. Browser Worker OOM (Out Of Memory) Crashes
- **Impact**: Active application executions die mid-flight; tasks get stuck in `EXECUTING` state.
- **Recovery**:
  1. Docker or Kubernetes will automatically restart the worker pod.
  2. The periodic `reconcile_unknown_submissions` task runs every 30 minutes. It finds applications stuck in `EXECUTING` for over 30 minutes, marks them as `FAILED` (Timeout), and releases the lock, allowing the user's daily limit counter to accurately reflect failed attempts.

### 3. Database Outage
- **Impact**: Full system unavailability.
- **Recovery**:
  1. Standard PostgreSQL point-in-time recovery.
  2. Once the DB is restored, run `docker-compose restart backend_web celery_general celery_browser` to re-establish connection pools.

### 4. Rogue Automation Loop
- **Impact**: The system rapidly applies to jobs incorrectly, consuming limits.
- **Recovery**:
  1. **Kill Switch**: Set `CELERY_TASK_ROUTES={}` temporarily or stop the `celery_browser` container.
  2. Use Django Admin to set `auto_apply_enabled=False` for affected users.

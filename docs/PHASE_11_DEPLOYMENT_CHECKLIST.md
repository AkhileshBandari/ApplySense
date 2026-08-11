# PHASE 11 DEPLOYMENT CHECKLIST

## PRE-FLIGHT
- [ ] Database credentials exist entirely in environment variables.
- [ ] `DJANGO_SECRET_KEY` is securely generated, > 50 characters, and exists entirely in environment variables.
- [ ] `DJANGO_DEBUG` is explicitly set to `False`.
- [ ] `ALLOWED_HOSTS` matches the production domain strictly.
- [ ] LLM API keys (`OPENAI_API_KEY`, etc.) are supplied safely.
- [ ] Redis broker URL is protected or restricted to private networking.

## INFRASTRUCTURE STARTUP
- [ ] Docker daemon is running and has sufficient storage.
- [ ] `docker-compose up -d db redis` completes successfully.
- [ ] Database container initializes fully without crash looping.

## MIGRATIONS
- [ ] Connect to `backend_web` container: `docker-compose run backend_web python manage.py migrate`.
- [ ] Migrations apply idempotently with zero pending changes.

## WORKERS
- [ ] `docker-compose up -d celery_general celery_browser celery_beat` complete successfully.
- [ ] Browser worker initializes with `shm_size: 2gb` to support Chromium memory limits.
- [ ] Celery logs confirm successful connection to Redis broker.

## FRONTEND
- [ ] Frontend `.env` variables mapped strictly for Vite production compile.
- [ ] `docker-compose up -d frontend` completes successfully.

## HEALTH & VERIFICATION
- [ ] `/api/health/liveness/` returns HTTP 200.
- [ ] `/api/health/readiness/` returns HTTP 200 (Redis and DB connected).
- [ ] Ops Dashboard renders cleanly without console secrets.
- [ ] Load external dependencies check.

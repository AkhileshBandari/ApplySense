# ApplySense Production Deployment Guide

## Prerequisites
- A virtual machine or cluster capable of running Docker Compose.
- At least 4GB of RAM (8GB+ recommended due to Playwright workers).
- PostgreSQL 15+ (if using external DB).
- Redis 7+ (if using external Redis).

## 1. Setup Environment Variables
Copy `.env.example` to `.env` and fill in the required values:
```bash
cp backend/.env.example .env
```
Ensure `DJANGO_SECRET_KEY` is a highly secure random string, and set `DJANGO_DEBUG=False`.

## 2. Boot the Infrastructure
Use Docker Compose to build and start the entire stack:
```bash
docker-compose up -d --build
```
This will start:
- `applysense_db`: PostgreSQL Database
- `applysense_redis`: Redis Message Broker
- `applysense_backend_web`: Django API via Gunicorn
- `applysense_celery_general`: Standard background tasks
- `applysense_celery_browser`: Headless Playwright worker (high RAM)
- `applysense_celery_beat`: Task Scheduler
- `applysense_frontend`: React SPA

## 3. Database Initialization
Once running, apply database migrations:
```bash
docker exec -it applysense_backend_web python manage.py migrate
```

## 4. Validating Deployment
Hit the health check endpoints:
- Liveness: `curl http://<DOMAIN>/api/health/liveness/`
- Readiness: `curl http://<DOMAIN>/api/health/readiness/`
- Automation: `curl http://<DOMAIN>/api/health/automation/`

## Scaling
If the application queue grows too large, scale the browser workers (ensure enough RAM on the host machine):
```bash
docker-compose up -d --scale celery_browser=3
```

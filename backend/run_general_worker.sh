#!/bin/bash
set -e

echo "Starting ApplySense General Celery Worker..."

# Wait for DB/Redis implicitly via Celery retry or orchestrator

# Start Celery worker for the 'default' queue
exec celery -A applysense worker -l INFO -Q celery,default -n general_worker@%h

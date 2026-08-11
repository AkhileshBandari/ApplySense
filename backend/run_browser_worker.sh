#!/bin/bash
set -e

echo "Starting ApplySense Browser Celery Worker..."

echo "Ensuring Playwright chromium is installed..."
python -m playwright install chromium

# Start Celery worker for the 'automation' queue with low concurrency to save memory
exec celery -A applysense worker -l INFO -Q automation -n browser_worker@%h --concurrency=2 --max-tasks-per-child=10

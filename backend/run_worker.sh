#!/bin/bash
set -e

echo "Starting ApplySense Auto Apply Worker initialization..."

# 1. Ensure Playwright browsers are installed.
# Using chromium_headless_shell to optimize memory footprint as implemented in the ServerBrowserExecutionService.
echo "Installing Playwright chromium_headless_shell..."
python -m playwright install chromium

# 2. Wait for Redis/DB if necessary (assuming handled by infra/compose, but good practice if standalone)
# ...

# 3. Start Celery worker for the 'automation' queue
echo "Starting Celery worker for queue: automation..."
celery -A applysense worker -l INFO -Q automation -n automation_worker@%h

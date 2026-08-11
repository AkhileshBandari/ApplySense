#!/bin/bash
set -e

echo "Starting ApplySense Celery Beat..."

exec celery -A applysense beat -l INFO

#!/bin/bash
set -e

echo "Starting ApplySense Gunicorn API Server..."

# Run migrations
python manage.py migrate --noinput

# Collect static files if configured (skip for now in staging unless we setup Nginx static serving for backend)
# python manage.py collectstatic --noinput

exec gunicorn applysense.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 2 --timeout 60 --access-logfile - --error-logfile -

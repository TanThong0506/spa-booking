#!/bin/sh

set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn on port ${PORT:-8000}..."
exec gunicorn spa_booking.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile -

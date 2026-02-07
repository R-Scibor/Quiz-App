#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Starting Gunicorn..."
exec "$@"

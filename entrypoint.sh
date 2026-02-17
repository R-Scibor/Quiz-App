#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Waiting for database to be ready..."

# Wait for PostgreSQL to be ready using Django's database connection
# Retry up to 30 times with 2 second intervals (60 seconds total)
MAX_RETRIES=30
RETRY_INTERVAL=2
RETRY_COUNT=0

until python -c "
import os
import django
# Ensure settings are configured
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()
from django.db import connection
connection.ensure_connection()
" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Error: Database is not available after $MAX_RETRIES attempts. Exiting."
        exit 1
    fi
    echo "Database not ready yet (attempt $RETRY_COUNT/$MAX_RETRIES). Retrying in $RETRY_INTERVAL seconds..."
    sleep $RETRY_INTERVAL
done

echo "Database is ready!"

echo "Copying frontend files to shared volume..."
mkdir -p /app/frontend_static
cp -r /app/frontend/dist/* /app/frontend_static/

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Starting command: $@"
exec "$@"

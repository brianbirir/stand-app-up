#!/bin/bash

# Exit on any error
set -e

echo "Starting Django application setup..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
python << END
import os
import django
from django.conf import settings
from django.db import connections
from django.core.management.color import no_style
import time
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'standapp.settings')
django.setup()

style = no_style()
connection = connections['default']

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        connection.ensure_connection()
        print("Database connection successful!")
        break
    except Exception as e:
        retry_count += 1
        print(f"Database connection failed (attempt {retry_count}/{max_retries}): {e}")
        if retry_count >= max_retries:
            print("Could not connect to database after maximum retries")
            sys.exit(1)
        time.sleep(2)
END

echo "Making migrations..."
python manage.py makemigrations

echo "Running migrations..."
python manage.py migrate

echo "Creating superuser if it doesn't exist..."
python manage.py shell << END
import os
from django.contrib.auth.models import User

# Get superuser credentials from environment variables with defaults
admin_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

# Check if superuser already exists
if not User.objects.filter(username=admin_username).exists():
    User.objects.create_superuser(
        username=admin_username,
        email=admin_email,
        password=admin_password
    )
    print(f"Superuser '{admin_username}' created successfully!")
else:
    print(f"Superuser '{admin_username}' already exists.")
END

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Django setup complete. Starting Gunicorn server..."

# Execute the main command (Gunicorn)
exec "$@"
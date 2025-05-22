#!/bin/bash

# entrypoint.sh - Docker entrypoint script for Django application

set -e

# Source conda
source /opt/conda/etc/profile.d/conda.sh

# Activate the datanalytics environment
conda activate datanalytics_env

# Change to Django project directory
cd /Datanalytics/datanalytics

# Function to wait for database
wait_for_db() {
    echo "Waiting for database..."
    while ! nc -z db 5432; do
        sleep 1
    done
    echo "Database is ready!"
}

# Function to wait for Redis
wait_for_redis() {
    echo "Waiting for Redis..."
    while ! nc -z redis 6379; do
        sleep 1
    done
    echo "Redis is ready!"
}

# Function to run Django setup commands
setup_django() {
    echo "Running Django setup..."
    
    # Wait for services
    wait_for_db
    wait_for_redis
    
    # Run Django commands
    echo "Making migrations..."
    python manage.py makemigrations
    
    echo "Running migrations..."
    python manage.py migrate
    
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
    
    echo "Creating superuser..."
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()
try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@gmail.com', 'admin123')
        print('Superuser created successfully')
    else:
        print('Superuser already exists')
except IntegrityError:
    print('Superuser creation failed - user may already exist')
EOF

    echo "Updating site domain..."
    python manage.py shell << EOF
from django.contrib.sites.models import Site
try:
    site = Site.objects.get_current()
    site.domain = 'localhost:8000'
    site.name = 'localhost:8000'
    site.save()
    print('Site object updated:', site.domain)
except Exception as e:
    print('Site update failed:', e)
EOF
}

# Check if this is the web service (first argument should be runserver related)
if [[ "$1" == *"runserver"* ]] || [[ "$1" == "python" && "$2" == "manage.py" && "$3" == "runserver" ]]; then
    echo "Starting web service..."
    setup_django
    
    echo "Starting Django development server..."
    exec python manage.py runserver 0.0.0.0:8000

# Check if this is the celery service
elif [[ "$1" == *"celery"* ]] || [[ "$1" == "celery" ]]; then
    echo "Starting Celery worker..."
    
    # Wait for services but don't run full setup
    wait_for_db
    wait_for_redis
    
    # Wait a bit more for web service to complete migrations
    echo "Waiting for web service to complete setup..."
    sleep 10
    
    echo "Starting Celery worker..."
    exec celery -A datanalytics worker --loglevel=info --concurrency=5

# For any other command, just execute it
else
    echo "Executing command: $@"
    exec "$@"
fi
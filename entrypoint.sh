#!/bin/bash

# entrypoint.sh - Fixed Docker entrypoint script for Django application

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
    until nc -z db 5432; do
        echo "Database is unavailable - sleeping"
        sleep 1
    done
    echo "Database is ready!"
}

# Function to wait for Redis
wait_for_redis() {
    echo "Waiting for Redis..."
    until nc -z redis 6379; do
        echo "Redis is unavailable - sleeping"
        sleep 1
    done
    echo "Redis is ready!"
}

# Function to run Django setup commands with proper migration order
setup_django() {
    echo "Running Django setup..."
    
    # Wait for services
    wait_for_db
    wait_for_redis
    
    # Additional wait to ensure database is fully ready
    sleep 5
    
    echo "Step 1: Creating initial migration for users app..."
    python manage.py makemigrations users --empty --name initial_user_migration || true
    
    echo "Step 2: Making migrations for users app (custom user model)..."
    python manage.py makemigrations users || echo "Users migrations already exist or failed"
    
    echo "Step 3: Applying users migrations first..."
    python manage.py migrate users || echo "Users migration failed, continuing..."
    
    echo "Step 4: Making migrations for other apps..."
    python manage.py makemigrations projects || echo "Projects migrations already exist or failed"
    python manage.py makemigrations || echo "General makemigrations failed"
    
    echo "Step 5: Applying all migrations..."
    python manage.py migrate || echo "Some migrations failed, continuing..."
    
    echo "Step 6: Collecting static files..."
    python manage.py collectstatic --noinput || echo "Static collection failed"
    
    echo "Step 7: Creating superuser..."
    python manage.py shell << 'EOF'
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    username = 'admin'
    email = 'admin@gmail.com'
    password = 'admin123'
    
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_superuser(username, email, password)
        print(f'Superuser "{username}" created successfully')
    else:
        print(f'Superuser "{username}" already exists')
        
except Exception as e:
    print(f'Error during superuser creation: {e}')
    print('This is normal if migrations are not complete yet')
EOF

    echo "Step 8: Setting up site..."
    python manage.py shell << 'EOF'
try:
    from django.contrib.sites.models import Site
    site = Site.objects.get_current()
    site.domain = 'localhost:8000'
    site.name = 'Datanalytics Local'
    site.save()
    print(f'Site updated: {site.domain}')
except Exception as e:
    print(f'Site setup failed: {e}')
EOF
    
    echo "Django setup completed!"
}

# Check if this is the web service
if [[ "$1" == *"runserver"* ]] || [[ "$1" == "python" && "$2" == "manage.py" && "$3" == "runserver" ]]; then
    echo "Starting web service..."
    setup_django
    
    echo "Starting Django development server..."
    exec python manage.py runserver 0.0.0.0:8000

# Check if this is the celery service
elif [[ "$1" == *"celery"* ]] || [[ "$1" == "celery" ]]; then
    echo "Starting Celery worker..."
    
    # Wait for services
    wait_for_db
    wait_for_redis
    
    # Wait longer for web service to complete setup
    echo "Waiting for web service to complete setup..."
    sleep 30
    
    echo "Starting Celery worker..."
    exec celery -A datanalytics worker --loglevel=info --concurrency=5

# For any other command, just execute it
else
    echo "Executing command: $@"
    exec "$@"
fi

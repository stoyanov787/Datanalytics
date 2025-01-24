# Datanalytics

(datanalytics_env for all except redis)
1. run redis-server if not runned
2. run this command in datanalytics directory celery -A datanalytics worker --loglevel=info
3. run mlflow server --host 127.0.0.1 --port 8080 in gizmo env
4. python manage.py runserver

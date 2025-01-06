# Datanalytics

(datanalytics_env for all except redis)
1. run redis-server if not runned
2. python manage.py runserver
3. run this command in datanalytics directory celery -A datanalytics worker --loglevel=info

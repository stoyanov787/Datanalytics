from celery import shared_task

@shared_task()
def data_preparation(project_name):
    pass

@shared_task()
def train_and_evaluate(project_name):
    pass
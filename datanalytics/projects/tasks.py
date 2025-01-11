from celery import shared_task
import os
import subprocess
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

@shared_task()
def data_preparation(project_name):
    env = 'gizmo'
    command = f'conda run -n {env} python main.py --project {project_name} --data_prep_module standard'
    working_dir = os.path.join(os.getcwd(), 'gizmo')

    logger.info(f"\n\nRunning command: {command} in directory: {working_dir}\n\n")
    
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        universal_newlines=True,
        env=os.environ.copy(),
        cwd=working_dir
    )
    
    stdout, stderr = process.communicate()
        
    # Check return code
    if process.returncode != 0:
        raise subprocess.CalledProcessError(
            process.returncode, 
            command, 
            output=stdout, 
            stderr=stderr
        )
        
    return {
        'status': 'success',
        'project_name': project_name,
        'data_prep_module': 'standard',
        'return_code': process.returncode,
        'stdout': stdout,
        'stderr': stderr
    }

@shared_task()
def train_and_evaluate(project_name):
    pass


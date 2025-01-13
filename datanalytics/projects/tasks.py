from celery import shared_task
import os
import subprocess
from datetime import datetime
from celery.utils.log import get_task_logger
from typing import Dict, Any, Tuple

logger = get_task_logger(__name__)

def run_command(command: str, working_dir: str) -> Tuple[str, str, int]:
    logger.info(f"Executing command: {command} in directory: {working_dir}")
    
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
    
    if process.returncode != 0:
        logger.error(f"Command failed with return code {process.returncode}")
        logger.error(f"stderr: {stderr}")
        raise subprocess.CalledProcessError(
            process.returncode,
            command,
            output=stdout,
            stderr=stderr
        )
        
    return stdout, stderr, process.returncode

def get_latest_session_id(train_or_eval: str, project_name: str, working_dir: str) -> str:
    sessions_dir = os.path.join(working_dir, 'sessions')
    starts_with = f"{train_or_eval}_{project_name}"

    print(f"Looking for sessions in directory: {sessions_dir}")
    
    if not os.path.exists(sessions_dir):
        logger.warning(f"No sessions directory found for project {project_name}")
        return "latest"
        
    sessions = [directory for directory in os.listdir(sessions_dir) 
               if directory.startswith(starts_with) and os.path.isdir(os.path.join(sessions_dir, directory))]
    if not sessions:
        return "latest"
        
    sessions.sort(key=lambda directory: os.path.getctime(os.path.join(sessions_dir, directory)), reverse=True)
    return sessions[0]

@shared_task(bind=True, max_retries=3)
def data_preparation(self, project_name: str) -> Dict[str, Any]:
    env = 'gizmo'
    working_dir = os.path.join(os.getcwd(), 'gizmo')
    command = f'conda run -n {env} python main.py --project {project_name} --data_prep_module standard'

    stdout, stderr, return_code = run_command(command, working_dir)
    
    return {
        'status': 'success',
        'project_name': project_name,
        'data_prep_module': 'standard',
        'return_code': return_code,
        'stdout': stdout,
        'stderr': stderr,
        'timestamp': datetime.now().isoformat()
    }

@shared_task(bind=True, max_retries=3)
def train_and_evaluate(self, project_name: str) -> Dict[str, Any]:
    env = 'gizmo'
    working_dir = os.path.join(os.getcwd(), 'gizmo')
    
    train_command = f'conda run -n {env} python main.py --project {project_name} --train_module standard'
    train_stdout, train_stderr, train_return_code = run_command(train_command, working_dir)
    
    session_id = get_latest_session_id("TRAIN", project_name, working_dir)
    
    eval_command = f'conda run -n {env} python main.py --project {project_name} --eval_module standard --session "{session_id}"'
    eval_stdout, eval_stderr, eval_return_code = run_command(eval_command, working_dir)
    
    return {
        'status': 'success',
        'project_name': project_name,
        'train_return_code': train_return_code,
        'train_stdout': train_stdout,
        'train_stderr': train_stderr,
        'eval_return_code': eval_return_code,
        'eval_stdout': eval_stdout,
        'eval_stderr': eval_stderr,
        'timestamp': datetime.now().isoformat()
    }

"""This module contains Celery tasks for data preparation, training, evaluation, and report generation."""

from celery import shared_task
import os
import subprocess
from datetime import datetime
from celery.utils.log import get_task_logger
from typing import Dict, Any, Tuple
import pandas as pd
from django.conf import settings
from .models import Project
import sweetviz
from django.core.files import File

logger = get_task_logger(__name__)

def run_command(command: str, working_dir: str) -> Tuple[str, str, int]:
    """Execute a shell command and return stdout, stderr, and return code.
    
    :param command: Shell command to execute
    :param working_dir: Working directory for the command
    :return: Tuple of (stdout, stderr, return_code)
    """
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
    
    return stdout, stderr, process.returncode

def get_latest_session_id(train_or_eval: str, project_name: str, working_dir: str) -> str:
    """Get the latest session ID for a given project and task type.
    
    :param train_or_eval: Type of session ('TRAIN' or 'EVAL')
    :param project_name: Name of the project
    :param working_dir: Working directory
    :return: Latest session ID or 'latest'
    """
    sessions_dir = os.path.join(working_dir, "sessions")
    starts_with = f"{train_or_eval}_{project_name}"

    logger.info(f"Looking for sessions in directory: {sessions_dir}")
    
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
    """Prepare data for the project.

    :param project_name: Name of the project
    :return: Dictionary with task result details
    """
    try:
        # Get the project by parsing the project name
        username, proj_name = project_name.split("_", 1)
        project = Project.objects.get(name=proj_name, user__username=username)
        
        env = "gizmo"
        working_dir = os.path.join(os.getcwd(), "gizmo")
        
        logger.info(f"Starting data preparation for project: {project_name}")
        
        command = f"conda run -n {env} python main.py --project {project_name} --data_prep_module standard"
        stdout, stderr, return_code = run_command(command, working_dir)
        
        logger.info(f"Data prep command completed with return code: {return_code}")
        
        # Construct and save output path
        output_path = os.path.abspath(os.path.join(
            settings.MEDIA_ROOT, 
            "output_data", 
            project_name
        ))
        
        # Update project with prep output path
        project.prep_output = output_path
        project.save()
        
        return {
            "status": "success",
            "project_name": project_name,
            "data_prep_module": "standard",
            "return_code": return_code,
            "stdout": stdout,
            "stderr": stderr,
            "output_path": output_path,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Error in data_preparation for project {project_name}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=5)
        return {
            "status": "failure",
            "project_name": project_name,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@shared_task(bind=True, max_retries=3)
def train_and_evaluate(self, project_name: str) -> Dict[str, Any]:
    """Training and evaluation 
    
    :param project_name: Name of the project
    :return: Dictionary with task result details
    """
    try:
        # Get the project by parsing the project name
        username, proj_name = project_name.split("_", 1)
        project = Project.objects.get(name=proj_name, user__username=username)
        
        env = "gizmo"
        working_dir = os.path.join(os.getcwd(), "gizmo")
        
        logger.info(f"Starting train and evaluate for project: {project_name}")
        
        # Run training
        train_command = f"conda run -n {env} python main.py --project {project_name} --train_module standard"
        train_stdout, train_stderr, train_return_code = run_command(train_command, working_dir)
        
        logger.info(f"Train command completed with return code: {train_return_code}")
        
        # Get training session and run evaluation
        session_id = get_latest_session_id("TRAIN", project_name, working_dir)
        eval_command = f'conda run -n {env} python main.py --project {project_name} --eval_module standard --session "{session_id}"'
        eval_stdout, eval_stderr, eval_return_code = run_command(eval_command, working_dir)
        
        logger.info(f"Eval command completed with return code: {eval_return_code}")
        
        # Get final output path
        eval_session = get_latest_session_id("EVAL", project_name, working_dir)
        output_path = os.path.join(working_dir, "sessions", eval_session)
        
        # Update project with train/eval output path
        project.train_eval_output = output_path
        project.save()
        
        return {
            "status": "success",
            "project_name": project_name,
            "train_return_code": train_return_code,
            "train_stdout": train_stdout,
            "train_stderr": train_stderr,
            "eval_return_code": eval_return_code,
            "eval_stdout": eval_stdout,
            "eval_stderr": eval_stderr,
            "output_path": output_path,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Error in train_and_evaluate for project {project_name}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=5)
        return {
            "status": 'failure',
            "project_name": project_name,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@shared_task(bind=True, max_retries=3)
def generate_sweetviz_report(self, username: str, project_name: str) -> Dict[str, Any]:
    """
    Generate Sweetviz report for data analysis.
    
    :param username: Username of the user
    :param project_name: Name of the project
    :return: Dictionary with task result details
    """
    try:
        # Get the project
        project = Project.objects.get(name=project_name)
        
        # Read the CSV
        logger.info(f"Reading CSV from {project.input_dataframe}")
        df = pd.read_csv(project.input_dataframe)
        
        # Convert DataFrame items to make compatible with older Sweetviz
        df_dict = {col: df[col] for col in df.columns}
        df_compat = pd.DataFrame(df_dict)
        
        # Generate Sweetviz report
        logger.info("Generating Sweetviz report...")
        my_report = sweetviz.analyze(
            source=df_compat,
            pairwise_analysis="off"
        )
        
        # Create reports directory
        report_dir = os.path.join(settings.MEDIA_ROOT, "reports", username)
        os.makedirs(report_dir, exist_ok=True)
        
        # Save report
        report_filename = f"{username}_{project_name}.html"
        report_path = os.path.join(report_dir, report_filename)
        logger.info(f"Saving report to {report_path}")
        
        my_report.show_html(
            filepath=report_path,
            open_browser=False
        )
        
        # Update project with report
        with open(report_path, "rb") as f:
            django_file = File(f, name=report_filename)
            project.sweetviz_report = django_file
            project.save()
        
        return {
            "status": "success",
            "project_name": project_name,
            "report_path": report_path,
            "timestamp": datetime.now().isoformat()
        }
        
    except Project.DoesNotExist:
        logger.error(f"Project not found: {project_name}")
        return {
            "status": "failure",
            "error": f"Project not found: {project_name}",
            "project_name": project_name,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        # Log the full exception
        logger.exception(f"Error generating Sweetviz report for project {project_name}")
        
        # If we haven't exhausted retries, retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=5)
        
        # Always return a dictionary, even on failure
        return {
            "status": "failure",
            "error": str(e),
            "project_name": project_name,
            "timestamp": datetime.now().isoformat()
        }
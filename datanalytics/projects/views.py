from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.http import require_http_methods
from .forms import ParamForm, ProjectForm
from .models import Project
from .tasks import data_preparation, train_and_evaluate, get_latest_session_id, generate_sweetviz_report
import pandas as pd
from celery.result import AsyncResult
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

def handle_task_response(task_result: AsyncResult) -> Dict[str, Any]:
    """
    Handle Celery task response with improved error handling and status reporting.
    """
    status = task_result.status.lower()
    response = {
        'status': status,
        'task_id': task_result.id,
    }
    
    try:
        # Log the full task state for debugging
        logger.info(f"Task status: {status}")
        
        # Handle pending states
        if status in ['pending', 'started', 'retry']:
            return {
                'status': 'running',
                'task_id': task_result.id,
                'message': f'Task is currently in {status} state'
            }

        # Check if the task is in a state that we can process
        if status in ['success', 'failure', 'done']:
            result = task_result.result
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                logger.error(f"Invalid result format: {result}")
                return {
                    'status': 'failure',
                    'error': 'Invalid task result format'
                }
            
            # Extract project name safely
            project_name = result.get('project_name', 'Unknown')
            
            # If it's a success, process the result
            if status == 'success':
                # Determine task type
                is_train_task = 'train_return_code' in result
                is_prep_task = 'data_prep_module' in result
                is_sweetviz_task = 'report_path' in result
                
                # Construct output path based on task type
                if is_train_task:
                    working_dir = os.path.join(os.getcwd(), 'gizmo')
                    eval_session = get_latest_session_id("EVAL", project_name, working_dir)
                    output_path = os.path.join(working_dir, 'sessions', eval_session)
                    task_type = 'train_and_eval'
                elif is_prep_task:
                    output_path = result.get('output_path')
                    task_type = 'prep'
                elif is_sweetviz_task:
                    output_path = result.get('report_path')
                    task_type = 'sweetviz'
                else:
                    logger.warning("Could not determine task type")
                    output_path = None
                    task_type = 'unknown'
                
                # Validate output path
                if output_path and not os.path.exists(output_path):
                    logger.warning(f"Output path does not exist: {output_path}")
                
                response.update({
                    'status': 'done',
                    'output': result,
                    'output_path': output_path,
                    'task_type': task_type
                })
            
            # If it's a failure, include the error
            elif status == 'failure':
                response.update({
                    'error': result.get('error', 'Unknown error occurred')
                })
            
            return response
        
        # If the task is in an unexpected state
        logger.warning(f"Unexpected task state: {status}")
        return {
            'status': 'failure',
            'error': f'Unexpected task state: {status}'
        }
        
    except Exception as e:
        logger.exception("Error handling task response")
        return {
            'status': 'failure',
            'error': f'Error processing task result: {str(e)}'
        }

@login_required
def param(request):
    return render(request, 'param/param.html', {
        'form': ParamForm(request=request)
    })

@login_required
def observation_date_column_choice(request):
    return render(request, 'param/dependent_fields.html', {
        'form': ParamForm(request=request)
    })

@login_required
def project_creation(request):
    return render(request, 'project_creation.html', {
        'form': ProjectForm()
    })

@login_required
def projects(request):
    project_name = request.GET.get('project_name')
    
    if not project_name:
        return render(request, 'projects/all_projects.html', {
            'projects': Project.objects.filter(user=request.user)
        })

    project = get_object_or_404(Project, user=request.user, name=project_name)
    full_project_name = f"{request.user.get_username()}_{project_name}"
    
    # Get active task IDs from session
    prep_task_id = request.session.get(f'prep_task_{project_name}')
    train_eval_task_id = request.session.get(f'train_eval_task_{project_name}')
    
    # Check task statuses
    prep_status = None
    train_eval_status = None
    prep_output_path = None
    train_eval_output_path = None
    
    working_dir = os.path.join(os.getcwd(), 'gizmo')
    
    if prep_task_id:
        result = AsyncResult(prep_task_id)
        if result.status in ['PENDING', 'STARTED', 'RETRY']:
            prep_status = 'running'
        elif result.status == 'SUCCESS':
            # For prep tasks, use the output_data directory
            prep_output_path = os.path.abspath(os.path.join(
                settings.MEDIA_ROOT, 'output_data', full_project_name
            ))
            
    if train_eval_task_id:
        result = AsyncResult(train_eval_task_id)
        if result.status in ['PENDING', 'STARTED', 'RETRY']:
            train_eval_status = 'running'
        elif result.status == 'SUCCESS':
            # For train/eval tasks, get latest eval session
            eval_session = get_latest_session_id("EVAL", full_project_name, working_dir)
            train_eval_output_path = os.path.join(working_dir, 'sessions', eval_session)

    # If paths don't exist from task results, try to construct them from filesystem
    if not prep_output_path:
        potential_prep_path = os.path.abspath(os.path.join(
            settings.MEDIA_ROOT, 'output_data', full_project_name
        ))
        if os.path.exists(potential_prep_path):
            prep_output_path = potential_prep_path

    if not train_eval_output_path:
        eval_session = get_latest_session_id("EVAL", full_project_name, working_dir)
        potential_eval_path = os.path.join(working_dir, 'sessions', eval_session)
        if os.path.exists(potential_eval_path) and eval_session != "latest":
            train_eval_output_path = potential_eval_path

    report_path = os.path.join(
        settings.MEDIA_ROOT, 
        'reports', 
        request.user.get_username(),
        f"{request.user.get_username()}_{project_name}.html"
    )
    report_exists = os.path.exists(report_path)
    
    # Get Sweetviz task status
    sweetviz_task_id = request.session.get(f'sweetviz_task_{project_name}')
    sweetviz_status = None
    if sweetviz_task_id:
        result = AsyncResult(sweetviz_task_id)
        if result.status in ['PENDING', 'STARTED', 'RETRY']:
            sweetviz_status = 'running'
    
    return render(request, 'projects/project.html', {
        'project': project,
        'prep_output_path': prep_output_path,
        'train_eval_output_path': train_eval_output_path,
        'prep_status': prep_status,
        'train_eval_status': train_eval_status,
        'prep_task_id': prep_task_id if prep_status == 'running' else None,
        'train_eval_task_id': train_eval_task_id if train_eval_status == 'running' else None,
        'report_exists': report_exists,
        'sweetviz_status': sweetviz_status,
        'sweetviz_task_id': sweetviz_task_id if sweetviz_status == 'running' else None,
    })

@login_required
@require_http_methods(['GET'])
def download_csv(request):
    project_name = request.GET.get('project_name')
    if not project_name:
        return redirect('/')

    project = get_object_or_404(Project, user=request.user, name=project_name)
    
    try:
        df = pd.read_csv(project.input_dataframe)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{project_name}_input.csv"'
        df.to_csv(response, index=False)
        return response
    except Exception as e:
        logger.exception(f"Error downloading CSV for project {project_name}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(['POST'])
def train_and_eval(request):
    try:
        project_name = request.POST.get("project_name")
        if not project_name:
            return JsonResponse({'error': 'Project name is required'}, status=400)
        
        project = get_object_or_404(Project, user=request.user, name=project_name)
        full_project_name = f"{request.user.username}_{project_name}"
        
        result = train_and_evaluate.delay(full_project_name)
        
        # Store task ID in session
        request.session[f'train_eval_task_{project_name}'] = result.id
        
        logger.info(f"Started train_and_eval task with ID: {result.id}")
        
        return JsonResponse({
            'status': 'success',
            'task_id': result.id,
            'message': 'Training and evaluation started'
        })
        
    except Project.DoesNotExist:
        logger.error(f"Project not found: {project_name}")
        return JsonResponse({
            'error': 'Project not found'
        }, status=404)
    except Exception as e:
        logger.exception(f"Error in train_and_eval view for project {project_name}")
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(['POST'])
def prep(request):
    try:
        project_name = request.POST.get("project_name")
        if not project_name:
            return JsonResponse({'error': 'Project name is required'}, status=400)
        
        project = get_object_or_404(Project, user=request.user, name=project_name)
        full_project_name = f"{request.user.username}_{project_name}"
        
        result = data_preparation.delay(full_project_name)
        
        # Store task ID in session
        request.session[f'prep_task_{project_name}'] = result.id
        
        logger.info(f"Started prep task with ID: {result.id}")
        
        return JsonResponse({
            'status': 'success',
            'task_id': result.id,
            'message': 'Data preparation started'
        })
        
    except Project.DoesNotExist:
        logger.error(f"Project not found: {project_name}")
        return JsonResponse({
            'error': 'Project not found'
        }, status=404)
    except Exception as e:
        logger.exception(f"Error in prep view for project {project_name}")
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(['GET'])
def task_status(request, task_id: str):
    try:
        result = AsyncResult(task_id)
        response = handle_task_response(result)
        return JsonResponse(response)
    except Exception as e:
        logger.exception(f"Error checking task status for task_id {task_id}")
        error_details = {
            'status': 'error',
            'error': str(e),
            'task_id': task_id,
            'error_type': type(e).__name__
        }
        return JsonResponse(error_details, status=500)
    
@login_required
@require_http_methods(['POST'])
def analyze_sweetviz(request):
    try:
        project_name = request.POST.get("project_name")
        if not project_name:
            return JsonResponse({'error': 'Project name is required'}, status=400)
        
        project = get_object_or_404(Project, user=request.user, name=project_name)
        result = generate_sweetviz_report.delay(request.user.get_username(), project_name)
        
        request.session[f'sweetviz_task_{project_name}'] = result.id
        
        return JsonResponse({'task_id': result.id})
        
    except Exception as e:
        logger.exception(f"Error in analyze_sweetviz view for project {project_name}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(['GET'])
def download_sweetviz(request):
    project_name = request.GET.get('project_name')
    if not project_name:
        return JsonResponse({'error': 'Project name is required'}, status=400)
        
    report_path = os.path.join(
        settings.MEDIA_ROOT, 
        'reports', 
        request.user.get_username(),
        f"{request.user.get_username()}_{project_name}.html"
    )
    
    if not os.path.exists(report_path):
        return JsonResponse({'error': 'Report not found'}, status=404)
        
    with open(report_path, 'r', encoding='utf-8') as f:
        response = HttpResponse(f.read(), content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="{project_name}.html"'
        return response
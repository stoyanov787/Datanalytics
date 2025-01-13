from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.http import require_http_methods
from .forms import ParamForm, ProjectForm
from .models import Project
from .tasks import data_preparation, train_and_evaluate, get_latest_session_id
import pandas as pd
from celery.result import AsyncResult
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

def handle_task_response(task_result: AsyncResult) -> Dict[str, Any]:
    status = task_result.status.lower()
    response = {
        'status': status,
        'task_id': task_result.id,
    }
    
    if status == 'success':
        result = task_result.result
        project_name = result.get('project_name')
        if project_name:
            # Determine if this is a train/eval task by checking for train-specific fields
            is_train_task = 'train_return_code' in result
            
            working_dir = os.path.join(os.getcwd(), 'gizmo')
            if is_train_task:
                # For train/eval tasks, get latest eval session
                eval_session = get_latest_session_id("EVAL", project_name, working_dir)
                output_path = os.path.join(working_dir, 'sessions', eval_session)
            else:
                # For prep tasks, use the output_data directory
                output_path = os.path.abspath(os.path.join(
                    settings.MEDIA_ROOT, 'output_data', project_name
                ))
            
            response.update({
                'status': 'done',
                'output': result,
                'output_path': output_path,
                'task_type': 'train' if is_train_task else 'prep'
            })
    elif status == 'failure':
        response['error'] = str(task_result.result)
    
    return response

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
    
    output_path = os.path.join(
        settings.MEDIA_ROOT, 
        'output_data',
        f"{request.user.get_username()}_{project_name}"
    )
    
    return render(request, 'projects/project.html', {
        'project': project,
        'output_path': output_path if os.path.exists(output_path) and os.path.isdir(output_path) else None
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
def prep(request):
    try:
        project_name = request.POST.get("project_name")
        if not project_name:
            return JsonResponse({'error': 'Project name is required'}, status=400)
        
        get_object_or_404(Project, user=request.user, name=project_name)
        project = f"{request.user.get_username()}_{project_name}"
        result = data_preparation.delay(project)
        
        return JsonResponse({'task_id': result.id})
        
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
    except Exception as e:
        logger.exception(f"Error in prep view for project {project_name}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(['POST'])
def train_and_eval(request):
    try:
        project_name = request.POST.get("project_name")
        if not project_name:
            return JsonResponse({'error': 'Project name is required'}, status=400)
        
        get_object_or_404(Project, user=request.user, name=project_name)
        project = f"{request.user.get_username()}_{project_name}"
        result = train_and_evaluate.delay(project)
        
        return JsonResponse({'task_id': result.id})
        
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
    except Exception as e:
        logger.exception(f"Error in train_and_eval view for project {project_name}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(['GET'])
def task_status(request, task_id: str):
    try:
        result = AsyncResult(task_id)
        return JsonResponse(handle_task_response(result))
    except Exception as e:
        logger.exception(f"Error checking task status for task_id {task_id}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

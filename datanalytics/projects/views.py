from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .forms import ParamForm, ProjectForm
from .models import Project
from .tasks import data_preparation
import pandas as pd
from celery.result import AsyncResult
import logging
import os

logger = logging.getLogger(__name__)

@login_required
def param(request):
    context = {}
    context['form'] = ParamForm(request=request)
    return render(request, 'param/param.html', context)



@login_required
def observation_date_column_choice(request):
    context = {}
    context['form'] = ParamForm(request=request)
    return render(request, 'param/dependent_fields.html', context)

@login_required
def project_creation(request):
    context = {}
    context['form'] = ProjectForm()
    return render(request, 'project_creation.html', context)
    
@login_required
def projects(request):
    project_name = request.GET.get('project_name')
    if not project_name:
        user_projects = Project.objects.filter(user=request.user)
        context = {
            'projects': user_projects
        }
        return render(request, 'projects/all_projects.html', context)

    project = get_object_or_404(Project, user=request.user, name=project_name)
    
    # Check if output directory exists
    output_path = os.path.join(settings.MEDIA_ROOT, 'output_data', 
                              f"{request.user.get_username()}_{project_name}")
    output_exists = os.path.exists(output_path) and os.path.isdir(output_path)

    context = {
        'project': project,
        'output_path': output_path if output_exists else None
    }
    return render(request, 'projects/project.html', context)

@login_required
def download_csv(request):
    project_name = request.GET.get('project_name')

    if not project_name:
        redirect('/')

    project = get_object_or_404(Project, user=request.user, name=project_name)
    df = pd.read_csv(project.input_dataframe)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="input.csv"'
    df.to_csv(response, index=False)
    
    return response

@login_required
def prep(request):
    if request.method == 'POST':
        try:
            project_name = request.POST.get("project_name")
            
            if not project_name:
                return JsonResponse({'error': 'Project name is required'}, status=400)
            
            project = request.user.get_username() + "_" + project_name
            result = data_preparation.delay(project)
            return JsonResponse({'task_id': result.id})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def task_status(request, task_id):
    result = AsyncResult(task_id)
    status = result.status
    
    response = {
        'status': status.lower(),
        'task_id': task_id,
    }
    
    if status == 'SUCCESS':
        project_name = result.result.get('project_name')
        if project_name:
            # Construct the full filesystem path
            output_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, 'output_data', project_name))
            response.update({
                'status': 'done',
                'output': result.result,
                'output_path': output_path  # This will be the full filesystem path
            })
    elif status == 'FAILURE':
        response['error'] = str(result.result)
    
    return JsonResponse(response)


@login_required
def serve_output_files(request, project_name):
    # Construct the full path
    project_name = request.user.get_username() + "_" + project_name
    output_path = os.path.join(settings.MEDIA_ROOT, 'output_data', project_name)
    
    # Check if path exists and is a directory
    if os.path.exists(output_path) and os.path.isdir(output_path):
        # Get list of files in directory
        files = os.listdir(output_path)
        return render(request, 'projects/directory_listing.html', {
            'files': files,
            'project_name': project_name,
            'directory_path': output_path
        })
    
    return HttpResponse('Directory not found', status=404)

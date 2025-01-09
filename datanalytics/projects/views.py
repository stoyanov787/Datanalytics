from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import ParamForm, ProjectForm
from .models import Project
from .tasks import data_preparation
import pandas as pd

def param(request):
    if request.user.is_authenticated:
        context = {}
        context['form'] = ParamForm(request=request)
        return render(request, 'param/param.html', context)
    else:
        return HttpResponse("You are not logged in")


def observation_date_column_choice(request):
    context = {}
    context['form'] = ParamForm(request=request)
    return render(request, 'param/dependent_fields.html', context)

def project_creation(request):
    if request.user.is_authenticated:
        context = {}
        context['form'] = ProjectForm()
        return render(request, 'project_creation.html', context)
    else:
        return HttpResponse("You are not logged in")
    
def projects(request):
    if not request.user.is_authenticated:
        return redirect('/accounts/login')
    
    project_name = request.GET.get('project_name')
    if not project_name:
        user_projects = Project.objects.filter(user=request.user)
        context = {
            'projects': user_projects
        }
        return render(request, 'projects/all_projects.html', context)

    project = get_object_or_404(Project, user=request.user, name=project_name)

    context = {
            'project': project
    }
    return render(request, 'projects/project.html', context)

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

def prep(request):
    project_name = request.POST.get("project_name")
    project = request.user.get_username() + "_" + project_name
    print(f"Project name: {project_name}")
    result = data_preparation.delay(project)
    task_output = result.get()  # This will block until task completes
    return HttpResponse(f"Output: {task_output}")


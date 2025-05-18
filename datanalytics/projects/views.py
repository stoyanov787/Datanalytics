"""Views for the projects app.

This module contains all the view functions for the projects app, handling HTTP requests
and responses for project management, data preparation, training, evaluation, and analysis.
"""

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
import sys
from typing import Dict, Any
import json
from django.contrib import messages

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to console
    ]
)

logger = logging.getLogger(__name__)


def handle_task_response(task_result: AsyncResult) -> Dict[str, Any]:
    """Handle Celery task response with improved error handling and status reporting.
    
    This function processes the result of a Celery task and returns a standardized
    response dictionary with appropriate status information and error handling.
    
    :param task_result: The AsyncResult object representing the Celery task
    :type task_result: AsyncResult
    :return: A dictionary containing the task status, ID, and additional information
    :rtype: Dict[str, Any]
    """
    status = task_result.status.lower()
    response = {
        "status": status,
        "task_id": task_result.id,
    }
    
    try:
        # Log the full task state for debugging
        logger.info(f"Task status: {status}")
        
        # Handle pending states
        if status in ["pending", "started", "retry"]:
            return {
                "status": "running",
                "task_id": task_result.id,
                "message": f"Task is currently in {status} state"
            }

        # Check if the task is in a state that we can process
        if status in ["success", "failure", "done"]:
            result = task_result.result
            
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                logger.error(f"Invalid result format: {result}")
                return {
                    "status": "failure",
                    "error": "Invalid task result format"
                }
            
            # Extract project name safely
            project_name = result.get("project_name", "Unknown")
            
            # If it's a success, process the result
            if status == "success":
                # Determine task type
                is_train_task = "train_return_code" in result
                is_prep_task = "data_prep_module" in result
                is_sweetviz_task = "report_path" in result
                
                # Construct output path based on task type
                if is_train_task:
                    working_dir = os.path.join(os.getcwd(), "gizmo")
                    eval_session = get_latest_session_id("EVAL", project_name, working_dir)
                    output_path = os.path.join(working_dir, "sessions", eval_session)
                    task_type = "train_and_eval"
                elif is_prep_task:
                    output_path = result.get("output_path")
                    task_type = "prep"
                elif is_sweetviz_task:
                    output_path = result.get("report_path")
                    task_type = "sweetviz"
                else:
                    logger.warning("Could not determine task type")
                    output_path = None
                    task_type = "unknown"
                
                # Validate output path
                if output_path and not os.path.exists(output_path):
                    logger.warning(f"Output path does not exist: {output_path}")
                
                response.update({
                    "status": "done",
                    "output": result,
                    "output_path": output_path,
                    "task_type": task_type
                })
            
            # If it's a failure, include the error
            elif status == "failure":
                response.update({
                    "error": result.get("error", "Unknown error occurred")
                })
            
            return response
        
        # If the task is in an unexpected state
        logger.warning(f"Unexpected task state: {status}")
        return {
            "status": "failure",
            "error": f"Unexpected task state: {status}"
        }
        
    except Exception as e:
        logger.exception("Error handling task response")
        return {
            "status": "failure",
            "error": f"Error processing task result: {str(e)}"
        }

@login_required
@require_http_methods(["GET", "POST"])
def param(request):
    """Handle the parameter form for configuring project parameters.
    
    This view displays and processes the form for configuring project parameters.
    On GET requests, it displays the form. On POST requests, it validates the form data,
    creates a JSON parameter file, and redirects to the projects page.
    
    :param request: The HTTP request
    :type request: HttpRequest
    :return: Rendered form page on GET or form errors, redirect on successful POST
    :rtype: HttpResponse
    """
    if request.method == "GET":
        return render(request, "param/param.html", {
            "form": ParamForm(request=request)
        })
    else:
        form = ParamForm(request.POST, request=request)
        if form.is_valid():
            project_name = request.POST.get("project_name")
            if not project_name:
                return redirect("param")

            # Create the params dictionary from form data
            params = {
                "criterion_column": form.cleaned_data["criterion_column"],
                "missing_treatment": {"Info": "Missing"},
                "observation_date_column": form.cleaned_data["observation_date_column"],
                "secondary_criterion_columns": form.cleaned_data["secondary_criterion_columns"],
                "t1df": form.cleaned_data["t1df"],
                "t2df": form.cleaned_data["t2df"],
                "t3df": form.cleaned_data["t3df"],
                "periods_to_exclude": form.cleaned_data["periods_to_exclude"],
                "columns_to_exclude": form.cleaned_data["columns_to_exclude"],
                "lr_features": [],
                "lr_features_to_include": [],
                "trees_features_to_include": [],
                "trees_features_to_exclude": [],
                "cut_offs": {
                    "xgb": [],
                    "lr": [],
                    "dt": [],
                    "rf": []
                },
                "under_sampling": 1,
                "optimal_binning_columns": form.cleaned_data["optimal_binning_columns"],
                "main_table": "input.csv",
                "columns_to_include": [],
                "custom_calculations": [],
                "additional_tables": []
            }

            param_file = os.path.abspath(os.path.join(
                settings.MEDIA_ROOT, "params", f"params_{request.user.get_username()}_{project_name}.json"
            ))

            # Save the params as JSON file
            with open(param_file, "w") as f:
                json.dump(params, f, indent=4)

            return redirect("projects")
        else:
            return render(request, "param/param.html", {
                "form": form
            })
        
@login_required
def observation_date_column_choice(request):
    """Handle AJAX request for date-dependent field choices based on selected date column.
    
    This view is called via HTMX to update form fields that depend on the selected
    observation date column. It renders a partial template with updated date-dependent
    field options.
    
    :param request: The HTTP request
    :type request: HttpRequest
    :return: Rendered partial form with updated date-dependent fields
    :rtype: HttpResponse
    """
    return render(request, "param/dependent_fields.html", {
        "form": ParamForm(request=request)
    })

@login_required
def project_creation(request):
    """Handle project creation form submission and display.
    
    This view displays the project creation form on GET requests and processes
    form submissions on POST requests. It validates the form data, creates a new
    project, and redirects to the parameter configuration page.
    
    :param request: The HTTP request
    :type request: HttpRequest
    :return: Rendered form on GET or form errors, redirect on successful POST
    :rtype: HttpResponse
    """
    if request.method == "POST":
        # Pass user through kwargs
        form = ProjectForm(data=request.POST, files=request.FILES, user=request.user)
        if form.is_valid():
            try:
                project = form.save()
                messages.success(request, "Project created successfully!")
                return redirect(f"/projects/project/params/?project_name={project.name}")
            except Exception as e:
                messages.error(request, f"Error creating project: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Pass user through kwargs
        form = ProjectForm(user=request.user)
    
    return render(request, "projects/project_creation.html", {
        "form": form,
        "title": "Create New Project"
    })

@login_required
def project_params(request):
    """Handle project parameters configuration form.
    
    This view displays and processes the form for configuring project parameters.
    It loads the existing project, displays its parameters for editing, and saves
    updated parameters on form submission.
    
    :param request: The HTTP request containing project_name parameter
    :type request: HttpRequest
    :return: Rendered form on GET or form errors, redirect on successful POST
    :rtype: HttpResponse
    :raises Http404: If the project doesn't exist
    """
    project_name = request.GET.get("project_name")
    if not project_name:
        messages.error(request, "Project name is required")
        return redirect("projects")
    
    project = get_object_or_404(Project, name=project_name, user=request.user)
    
    if request.method == "POST":
        form = ParamForm(data=request.POST, project=project)
        if form.is_valid():
            try:
                form.save(project)
                messages.success(request, "Parameters saved successfully!")
                return redirect("projects")
            except Exception as e:
                messages.error(request, f"Error saving parameters: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ParamForm(project=project)
    
    return render(request, "projects/project_params.html", {
        "form": form,
        "project": project,
        "title": "Configure Parameters"
    })

@login_required
@require_http_methods(["GET"])
def get_date_values(request):
    """Get date values from a specific column in the project's CSV file.
    
    This AJAX endpoint retrieves all unique values from a date column in the
    project's CSV file. It parses the dates and returns them as formatted strings,
    along with suggestions for initial values for t1df, t2df, and t3df fields.
    
    :param request: The HTTP request with column and project_name parameters
    :type request: HttpRequest
    :return: JSON response with available dates and initial values
    :rtype: JsonResponse
    :raises Http404: If the project doesn't exist
    """
    try:
        column = request.GET.get("column")
        project_name = request.GET.get("project_name")
        
        if not column or not project_name:
            return JsonResponse({"error": "Missing parameters"}, status=400)
            
        project = get_object_or_404(Project, name=project_name, user=request.user)
        df = pd.read_csv(project.input_dataframe)
        
        try:
            # Convert to datetime and handle NaT values
            df[column] = pd.to_datetime(df[column], errors="coerce")
            
            # Filter out NaT values before sorting
            valid_dates = df[df[column].notna()][column].unique()
            valid_dates = sorted(valid_dates)
            
            # Format dates, explicitly skipping NaT values
            formatted_dates = []
            for d in valid_dates:
                if pd.notna(d):  # Skip NaT values
                    formatted_dates.append(pd.Timestamp(d).strftime("%m/%d/%Y"))
            
            if not formatted_dates:
                return JsonResponse({"error": "No valid dates found"}, status=400)
                
            return JsonResponse({
                "dates": formatted_dates,
                "initial_values": {
                    "t1df": formatted_dates[0],
                    "t2df": formatted_dates[len(formatted_dates)//2],
                    "t3df": formatted_dates[-1]
                }
            })
        except Exception as e:
            return JsonResponse({"error": f"Error processing dates: {str(e)}"}, status=500)
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def projects(request):
    """Display all projects or a specific project detail view.
    
    This view serves two purposes:
    1. If no project_name is provided, it displays a list of all user's projects
    2. If a project_name is provided, it displays the detail view for that project
       including its current status, output paths, and task information
    
    :param request: The HTTP request
    :type request: HttpRequest
    :return: Rendered project list or detail view
    :rtype: HttpResponse
    :raises Http404: If the specific project doesn't exist
    """
    project_name = request.GET.get("project_name")
    
    if not project_name:
        return render(request, "projects/all_projects.html", {
            "projects": Project.objects.filter(user=request.user)
        })

    project = get_object_or_404(Project, user=request.user, name=project_name)
    
    # Get active task IDs from session
    prep_task_id = request.session.get(f"prep_task_{project_name}")
    train_eval_task_id = request.session.get(f"train_eval_task_{project_name}")
    
    # Check task statuses
    prep_status = None
    train_eval_status = None
    
    if prep_task_id:
        result = AsyncResult(prep_task_id)
        if result.status in ["PENDING", "STARTED", "RETRY"]:
            prep_status = "running"
            
    if train_eval_task_id:
        result = AsyncResult(train_eval_task_id)
        if result.status in ["PENDING", "STARTED", "RETRY"]:
            train_eval_status = "running"
    
    # Get Sweetviz task status
    sweetviz_task_id = request.session.get(f"sweetviz_task_{project_name}")
    sweetviz_status = None
    if sweetviz_task_id:
        result = AsyncResult(sweetviz_task_id)
        if result.status in ["PENDING", "STARTED", "RETRY"]:
            sweetviz_status = "running"
    
    return render(request, "projects/project.html", {
        "project": project,
        "prep_output_path": project.prep_output,
        "train_eval_output_path": project.train_eval_output,
        "prep_status": prep_status,
        "train_eval_status": train_eval_status,
        "prep_task_id": prep_task_id if prep_status == "running" else None,
        "train_eval_task_id": train_eval_task_id if train_eval_status == "running" else None,
        "report_exists": bool(project.sweetviz_report),
        "sweetviz_status": sweetviz_status,
        "sweetviz_task_id": sweetviz_task_id if sweetviz_status == "running" else None,
    })

@login_required
@require_http_methods(["GET"])
def download_csv(request):
    """Download the input CSV file for a project.
    
    This view retrieves the project's input CSV file and sends it as a downloadable
    file attachment. The file name is based on the project name.
    
    :param request: The HTTP request with project_name parameter
    :type request: HttpRequest
    :return: CSV file as HTTP response for download
    :rtype: HttpResponse
    :raises Http404: If the project doesn't exist
    """
    project_name = request.GET.get("project_name")
    if not project_name:
        return redirect("/")

    project = get_object_or_404(Project, user=request.user, name=project_name)
    
    try:
        df = pd.read_csv(project.input_dataframe)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{project_name}_input.csv"'
        df.to_csv(response, index=False)
        return response
    except Exception as e:
        logger.exception(f"Error downloading CSV for project {project_name}")
        return JsonResponse({"error": str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def train_and_eval(request):
    """Start the training and evaluation task for a project.
    
    This view initiates a Celery task to train models and evaluate their performance
    on the project data. It stores the task ID in the session for status tracking.
    
    :param request: The HTTP request with project_name parameter
    :type request: HttpRequest
    :return: JSON response with task status information
    :rtype: JsonResponse
    :raises Http404: If the project doesn't exist
    """
    try:
        project_name = request.POST.get("project_name")
        if not project_name:
            return JsonResponse({"error": "Project name is required"}, status=400)
        
        project = get_object_or_404(Project, user=request.user, name=project_name)
        full_project_name = f"{request.user.username}_{project_name}"
        
        result = train_and_evaluate.delay(full_project_name)
        
        # Store task ID in session
        request.session[f"train_eval_task_{project_name}"] = result.id
        
        logger.info(f"Started train_and_eval task with ID: {result.id}")
        
        return JsonResponse({
            "status": "success",
            "task_id": result.id,
            "message": "Training and evaluation started"
        })
        
    except Project.DoesNotExist:
        logger.error(f"Project not found: {project_name}")
        return JsonResponse({
            "error": "Project not found"
        }, status=404)
    except Exception as e:
        logger.exception(f"Error in train_and_eval view for project {project_name}")
        return JsonResponse({
            "error": str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def prep(request):
    """Start the data preparation task for a project.
    
    This view initiates a Celery task to prepare and preprocess the project data.
    It stores the task ID in the session for status tracking. The data preparation
    task performs feature engineering, data cleaning, and other preprocessing steps.
    
    :param request: The HTTP request with project_name parameter
    :type request: HttpRequest
    :return: JSON response with task status information
    :rtype: JsonResponse
    :raises Http404: If the project doesn't exist
    """
    try:
        project_name = request.POST.get("project_name")
        if not project_name:
            return JsonResponse({"error": "Project name is required"}, status=400)
        
        project = get_object_or_404(Project, user=request.user, name=project_name)
        full_project_name = f"{request.user.username}_{project_name}"
        
        result = data_preparation.delay(full_project_name)
        
        # Store task ID in session
        request.session[f"prep_task_{project_name}"] = result.id
        
        logger.info(f"Started prep task with ID: {result.id}")
        
        return JsonResponse({
            "status": "success",
            "task_id": result.id,
            "message": "Data preparation started"
        })
        
    except Project.DoesNotExist:
        logger.error(f"Project not found: {project_name}")
        return JsonResponse({
            "error": "Project not found"
        }, status=404)
    except Exception as e:
        logger.exception(f"Error in prep view for project {project_name}")
        return JsonResponse({
            "error": str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def task_status(request, task_id: str):
    """Check the status of a Celery task.
    
    This view retrieves the current status of a Celery task by its ID. It processes
    the raw task result into a standardized format using the handle_task_response function.
    
    :param request: The HTTP request
    :type request: HttpRequest
    :param task_id: The ID of the Celery task to check
    :type task_id: str
    :return: JSON response with detailed task status information
    :rtype: JsonResponse
    """
    try:
        result = AsyncResult(task_id)
        response = handle_task_response(result)
        return JsonResponse(response)
    except Exception as e:
        logger.exception(f"Error checking task status for task_id {task_id}")
        error_details = {
            "status": "error",
            "error": str(e),
            "task_id": task_id,
            "error_type": type(e).__name__
        }
        return JsonResponse(error_details, status=500)
    
@login_required
@require_http_methods(["POST"])
def analyze_sweetviz(request):
    """Start the Sweetviz report generation task for a project.
    
    This view initiates a Celery task to generate a Sweetviz report for the project data.
    Sweetviz is a data exploration library that creates visual EDA (Exploratory Data Analysis)
    reports. The task ID is stored in the session for status tracking.
    
    :param request: The HTTP request with project_name parameter
    :type request: HttpRequest
    :return: JSON response with task ID
    :rtype: JsonResponse
    :raises Http404: If the project doesn't exist
    """
    try:
        project_name = request.POST.get("project_name")
        if not project_name:
            return JsonResponse({"error": "Project name is required"}, status=400)
        
        project = get_object_or_404(Project, user=request.user, name=project_name)
        result = generate_sweetviz_report.delay(request.user.get_username(), project_name)
        
        request.session[f"sweetviz_task_{project_name}"] = result.id
        
        return JsonResponse({"task_id": result.id})
        
    except Exception as e:
        logger.exception(f"Error in analyze_sweetviz view for project {project_name}")
        return JsonResponse({"error": str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def download_sweetviz(request):
    """Download the Sweetviz report for a project.
    
    This view retrieves the generated Sweetviz HTML report and sends it as a
    downloadable file attachment. The file name is based on the project name.
    
    :param request: The HTTP request with project_name parameter
    :type request: HttpRequest
    :return: HTML file as HTTP response for download
    :rtype: HttpResponse
    :raises Http404: If the report doesn't exist
    """
    project_name = request.GET.get("project_name")
    if not project_name:
        return JsonResponse({"error": "Project name is required"}, status=400)
        
    report_path = os.path.join(
        settings.MEDIA_ROOT, 
        "reports", 
        request.user.get_username(),
        f"{request.user.get_username()}_{project_name}.html"
    )
    
    if not os.path.exists(report_path):
        return JsonResponse({"error": "Report not found"}, status=404)
        
    with open(report_path, "r", encoding="utf-8") as f:
        response = HttpResponse(f.read(), content_type="text/html")
        response["Content-Disposition"] = f'attachment; filename="{project_name}.html"'
        return response
    
@login_required
@require_http_methods(["GET"])
def show_report(request):
    """Display the Sweetviz report for a project in the browser.
    
    This view retrieves the generated Sweetviz HTML report and displays it directly
    in the browser. Unlike the download_sweetviz view, this returns the HTML content
    without the Content-Disposition header, so the browser renders it instead of
    downloading it.
    
    :param request: The HTTP request with project_name parameter
    :type request: HttpRequest
    :return: HTML content as HTTP response for rendering in browser
    :rtype: HttpResponse
    :raises Http404: If the report doesn't exist
    """
    project_name = request.GET.get("project_name")
    if not project_name:
        return JsonResponse({"error": "Project name is required"}, status=400)
    
    report_path = os.path.join(
        settings.MEDIA_ROOT, 
        "reports", 
        request.user.get_username(),
        f"{request.user.get_username()}_{project_name}.html"
    )
    
    if not os.path.exists(report_path):
        return JsonResponse({"error": "Report not found"}, status=404)
    
    with open(report_path, "r", encoding="utf-8") as f:
        return HttpResponse(f.read(), content_type="text/html")
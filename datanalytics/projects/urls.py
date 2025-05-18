"""URL configuration for the projects app."""

from django.urls import path
from . import views

urlpatterns = [
    # Project management
    path("", views.projects, name="projects"),
    path("newproject/", views.project_creation, name="project_creation"),
    path("project/params/", views.project_params, name="project_params"),
    
    # Data processing
    path("prep/", views.prep, name="prep"),
    path("trainandeval/", views.train_and_eval, name="train_and_eval"),
    
    # File operations
    path("download_csv/", views.download_csv, name="download_csv"),
    path("analyze_sweetviz/", views.analyze_sweetviz, name="analyze_sweetviz"),
    path("download_sweetviz/", views.download_sweetviz, name="download_sweetviz"),
    
    # AJAX endpoints
    path("get-date-values/", views.get_date_values, name="get_date_values"),
    path("task-status/<str:task_id>/", views.task_status, name="task_status"),
    path("reports/show/", views.show_report, name="show_report"),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.projects),
    path('prep/', views.prep),
    path('trainandeval/', views.train_and_eval),
    path('download_csv/', views.download_csv),
    path('project_creation/', views.project_creation),
    path('param/', views.param),
    path('param/observation_date_column_choice/', views.observation_date_column_choice, name='observation_date_column_choice'),
    path('task-status/<str:task_id>/', views.task_status, name='task_status'),
    path('analyze_sweetviz/', views.analyze_sweetviz, name='analyze_sweetviz'),
    path('download_sweetviz/', views.download_sweetviz, name='download_sweetviz'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.projects),
    path('download_csv/', views.download_csv),
    path('project_creation/', views.project_creation),
    path('param/', views.param),
    path('observation_date_column_choice/', views.observation_date_column_choice, name='observation_date_column_choice')
]

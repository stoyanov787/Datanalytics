from django.urls import path
from . import views

urlpatterns = [
    path('', views.param),
    path('observation_date_column_choice/', views.observation_date_column_choice, name='observation_date_column_choice')
]

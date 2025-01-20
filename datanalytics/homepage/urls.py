from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='homepage'),
    path('aboutus/', views.about_us, name='about_us')
]
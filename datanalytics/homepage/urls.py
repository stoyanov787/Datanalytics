"""URL configuration for the homepage app."""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("aboutus/", views.about_us, name="about_us")
]
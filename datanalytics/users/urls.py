"""URL configuration for the users app."""

from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.profile, name="profile"),
]
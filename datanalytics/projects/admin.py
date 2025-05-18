"""Admin configuration for the Project model."""

from django.contrib import admin
from .models import Project

admin.site.register(Project)
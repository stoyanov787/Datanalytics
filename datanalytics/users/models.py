"""Models for the users app."""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    """Custom user model that extends AbstractUser."""
    email = models.EmailField(_("email address"), unique=True, blank=False)

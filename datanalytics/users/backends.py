"""Extends the default authentication backend to allow login with email or username."""

from typing import Optional
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.http import HttpRequest
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to console
    ]
)

logger = logging.getLogger(__name__)

class EmailBackend(ModelBackend):
    """Custom authentication backend that allows login with email or username."""
    def authenticate(
        self, 
        request: Optional[HttpRequest], 
        username: Optional[str] = None, 
        password: Optional[str] = None, 
        **kwargs
    ) -> Optional[AbstractBaseUser]:
        """Authenticate a user using either their username or email address.
        
        :param request: The HTTP request object.
        :type request: HttpRequest
        :param username: The username or email address of the user.
        :type username: str
        :param password: The password of the user.
        :type password: str
        :return: The authenticated user or None if authentication fails.
        :rtype: AbstractBaseUser or None
        """

        logger.debug("Attempting to authenticate user with username/email: %s", username)
        user_model = get_user_model()
        try:
            user = user_model.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
            logger.debug("User found: %s", user)
        except user_model.DoesNotExist:
            logger.warning("Authentication failed: User with username/email '%s' does not exist.", username)
            return None
        else:
            if user.check_password(password):
                logger.info("Authentication successful for user: %s", user)
                return user
            else:
                logger.warning("Authentication failed: Incorrect password for user '%s'.", username)
        return None
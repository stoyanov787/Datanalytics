"""Tests for the users app."""

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from .forms import CustomUserForm, UserProfileForm
from .models import CustomUser
from .backends import EmailBackend
from django.conf import settings

class UserModelTests(TestCase):
    """Tests for the CustomUser model."""
    def setUp(self) -> None:
        """Set up the test case with a user instance."""
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="testuser",
            email=f"test@{settings.CORPORATE_EMAIL_DOMAIN}",
            password="testpass123"
        )

    def test_user_creation(self) -> None:
        """Test user creation with valid data."""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, f"test@{settings.CORPORATE_EMAIL_DOMAIN}")
        self.assertTrue(self.user.check_password("testpass123"))

    def test_user_string_representation(self) -> None:
        """Test the string representation of the user."""
        self.assertEqual(str(self.user), "testuser")

    def test_email_unique(self) -> None:
        """Test that email is unique."""
        with self.assertRaises(Exception):
            self.User.objects.create_user(
                username="testuser2",
                email=f"test@{settings.CORPORATE_EMAIL_DOMAIN}",
                password="testpass123"
            )

class UserFormTests(TestCase):
    """Tests for the CustomUserForm."""
    def test_valid_registration_form(self) -> None:
        """Test the registration form with valid data."""
        form_data = {
            "username": "newuser",
            "email": f"new@{settings.CORPORATE_EMAIL_DOMAIN}",
            "password1": "newpass123",
            "password2": "newpass123"
        }
        form = CustomUserForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_email_domain(self) -> None:
        """Test the registration form with an invalid email domain."""
        form_data = {
            "username": "newuser",
            "email": "new@invalid.com",
            "password1": "newpass123",
            "password2": "newpass123"
        }
        form = CustomUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_duplicate_email(self) -> None:
        """Test the registration form with a duplicate email."""
        CustomUser.objects.create_user(
            username="existinguser",
            email=f"existing@{settings.CORPORATE_EMAIL_DOMAIN}",
            password="pass123"
        )
        form_data = {
            "username": "newuser",
            "email": f"existing@{settings.CORPORATE_EMAIL_DOMAIN}",
            "password1": "newpass123",
            "password2": "newpass123"
        }
        form = CustomUserForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_duplicate_username(self) -> None:
        """Test the registration form with a duplicate username."""
        CustomUser.objects.create_user(
            username="existinguser",
            email=f"test1@{settings.CORPORATE_EMAIL_DOMAIN}",
            password="pass123"
        )
        form_data = {
            "username": "existinguser",
            "email": f"test2@{settings.CORPORATE_EMAIL_DOMAIN}",
            "password1": "newpass123",
            "password2": "newpass123"
        }
        form = CustomUserForm(data=form_data)
        self.assertFalse(form.is_valid())

class UserProfileFormTests(TestCase):
    """Tests for the UserProfileForm."""
    def setUp(self) -> None:
        """Set up the test case with a user instance."""
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email=f"test@{settings.CORPORATE_EMAIL_DOMAIN}",
            password="testpass123"
        )

    def test_valid_profile_update(self) -> None:
        """Test the profile update form with valid data."""
        form_data = {
            "username": "updateduser",
            "email": f"test@{settings.CORPORATE_EMAIL_DOMAIN}"
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

class UserViewTests(TestCase):
    """Tests for the user views."""
    def setUp(self) -> None:
        """Set up the test case with a client and user instance."""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email=f'test@{settings.CORPORATE_EMAIL_DOMAIN}',
            password="testpass123"
        )
        self.factory = RequestFactory()

    def test_profile_view_authenticated(self) -> None:
        """Test the profile view for authenticated users."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")

    def test_profile_view_unauthenticated(self) -> None:
        """Test the profile view for unauthenticated users."""
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)

    def test_profile_update(self) -> None:
        """Test the profile update view."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("profile"), {
            "username": "updateduser",
            "email": f"test@{settings.CORPORATE_EMAIL_DOMAIN}"
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updateduser")

class EmailBackendTests(TestCase):
    """Tests for the custom email authentication backend."""
    def setUp(self) -> None:
        """Set up the test case with a client and user instance."""
        self.backend = EmailBackend()
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email=f"test@{settings.CORPORATE_EMAIL_DOMAIN}",
            password="testpass123"
        )

    def test_authenticate_with_email(self) -> None:
        """Test authentication with email."""
        authenticated_user = self.backend.authenticate(
            None,
            username=f"test@{settings.CORPORATE_EMAIL_DOMAIN}",
            password="testpass123"
        )
        self.assertEqual(authenticated_user, self.user)

    def test_authenticate_with_username(self) -> None:
        """Test authentication with username."""
        authenticated_user = self.backend.authenticate(
            None,
            username="testuser",
            password="testpass123"
        )
        self.assertEqual(authenticated_user, self.user)

    def test_authenticate_invalid_credentials(self) -> None:
        """Test authentication with invalid credentials."""
        authenticated_user = self.backend.authenticate(
            None,
            username=f"test@{settings.CORPORATE_EMAIL_DOMAIN}",
            password="wrongpass"
        )
        self.assertIsNone(authenticated_user)

class CeleryEmailBackendTests(TestCase):
    """Tests for the Celery email backend."""
    def test_email_queuing(self) -> None:
        """Test that emails are queued correctly."""
        mail.send_mail(
            "Test Subject",
            "Test Body",
            "from@example.com",
            ["to@example.com"],
            fail_silently=False,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test Subject")

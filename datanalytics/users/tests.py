from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from .forms import CustomUserForm, UserProfileForm
from .models import CustomUser
from .backends import EmailBackend
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware

class UserModelTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@gmail.com',
            password='testpass123'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@gmail.com')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_string_representation(self):
        self.assertEqual(str(self.user), 'testuser')

    def test_email_unique(self):
        with self.assertRaises(Exception):
            self.User.objects.create_user(
                username='testuser2',
                email='test@gmail.com',
                password='testpass123'
            )

class UserFormTests(TestCase):
    def test_valid_registration_form(self):
        form_data = {
            'username': 'newuser',
            'email': 'new@gmail.com',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = CustomUserForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_email_domain(self):
        form_data = {
            'username': 'newuser',
            'email': 'new@invalid.com',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = CustomUserForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_email(self):
        CustomUser.objects.create_user(
            username='existinguser',
            email='existing@gmail.com',
            password='pass123'
        )
        form_data = {
            'username': 'newuser',
            'email': 'existing@gmail.com',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = CustomUserForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_duplicate_username(self):
        CustomUser.objects.create_user(
            username='existinguser',
            email='test1@gmail.com',
            password='pass123'
        )
        form_data = {
            'username': 'existinguser',
            'email': 'test2@gmail.com',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = CustomUserForm(data=form_data)
        self.assertFalse(form.is_valid())

class UserProfileFormTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@gmail.com',
            password='testpass123'
        )

    def test_valid_profile_update(self):
        form_data = {
            'username': 'updateduser',
            'email': 'test@gmail.com'
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

class UserViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@gmail.com',
            password='testpass123'
        )
        self.factory = RequestFactory()

    def test_profile_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

    def test_profile_view_unauthenticated(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)

    def test_profile_update(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('profile'), {
            'username': 'updateduser',
            'email': 'test@gmail.com'
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')

class EmailBackendTests(TestCase):
    def setUp(self):
        self.backend = EmailBackend()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@gmail.com',
            password='testpass123'
        )

    def test_authenticate_with_email(self):
        authenticated_user = self.backend.authenticate(
            None,
            username='test@gmail.com',
            password='testpass123'
        )
        self.assertEqual(authenticated_user, self.user)

    def test_authenticate_with_username(self):
        authenticated_user = self.backend.authenticate(
            None,
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(authenticated_user, self.user)

    def test_authenticate_invalid_credentials(self):
        authenticated_user = self.backend.authenticate(
            None,
            username='test@gmail.com',
            password='wrongpass'
        )
        self.assertIsNone(authenticated_user)

class CeleryEmailBackendTests(TestCase):
    def test_email_queuing(self):
        mail.send_mail(
            'Test Subject',
            'Test Body',
            'from@example.com',
            ['to@example.com'],
            fail_silently=False,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Test Subject')

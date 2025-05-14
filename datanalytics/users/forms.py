"""Forms for user registration and profile management."""

from django import forms
from django.contrib.auth import get_user_model
from django_registration.forms import RegistrationForm
from django.core.exceptions import ValidationError
from users.models import CustomUser
from django.conf import settings


class CustomUserForm(RegistrationForm):
    """Custom registration form for the CustomUser model."""
    class Meta(RegistrationForm.Meta):
        """Meta class for the CustomUserForm."""
        model = CustomUser
        fields = ["username", "email"]

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the form with custom attributes."""
        super().__init__(*args, **kwargs)
        # Add help texts and customize field widgets
        self.fields["email"].widget.attrs.update({
            "class": "form-contro",
            "placeholder": "Enter your corporate email"
        })
        self.fields["email"].help_text = "Use your corporate email address"
        
        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Choose a username"
        })

    def clean_email(self) -> str:
        """Validate the email field."""
        email = self.cleaned_data["email"]

        if not email.endswith(f"@{settings.CORPORATE_EMAIL_DOMAIN}"):
            raise ValidationError("Please use your Postbank email address.")
        
        # Check if email is already registered
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email address is already registered.")
            
        return email

    def clean_username(self) -> str:
        """Validate the username field."""
        username = self.cleaned_data["username"]
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def save(self, commit=True) -> CustomUser:
        """Save the user instance after validation."""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["username"]
        
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information."""
    class Meta:
        """Meta class for the UserProfileForm."""
        model = get_user_model()
        fields = ["email", "username"]
        
    def __init__(self, *args, **kwargs) -> None:
        """Initialize the form with custom attributes."""
        super().__init__(*args, **kwargs)
        # Make email readonly for profile updates
        self.fields['email'].widget.attrs.update({
            'readonly': True,
            'class': 'form-control'
        })
        self.fields['username'].widget.attrs.update({
            'class': 'form-control'
        })
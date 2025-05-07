from django import forms
from django.contrib.auth import get_user_model
from django_registration.forms import RegistrationForm
from django.core.exceptions import ValidationError
from users.models import CustomUser

class CustomUserForm(RegistrationForm):
    class Meta(RegistrationForm.Meta):
        model = CustomUser
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help texts and customize field widgets
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your corporate email'
        })
        self.fields['email'].help_text = 'Use your corporate email address'
        
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })

    def clean_email(self):
        email = self.cleaned_data['email']
        #if not email.endswith('@postbank.bg'):
        #use env variable
        if not email.endswith('@gmail.com'):
            raise ValidationError('Please use your Postbank email address.')
        
        # Check if email is already registered
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered.')
            
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']
        
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['email', 'username']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email readonly for profile updates
        self.fields['email'].widget.attrs.update({
            'readonly': True,
            'class': 'form-control'
        })
        self.fields['username'].widget.attrs.update({
            'class': 'form-control'
        })
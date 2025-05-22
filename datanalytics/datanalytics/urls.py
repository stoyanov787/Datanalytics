"""
URL configuration for datanalytics project.

The `urlpatterns` list routes URLs to views. For more information please see:
   https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

# Lazy loading function to avoid Docker import issues
def get_registration_view():
    """Get registration view with proper imports after Django is fully loaded."""
    from django_registration.backends.activation.views import RegistrationView
    from users.forms import CustomUserForm
    
    return RegistrationView.as_view(
        form_class=CustomUserForm,
    )

def get_activation_view():
    """Get activation view with proper imports after Django is fully loaded."""
    from django_registration.backends.activation.views import ActivationView
    return ActivationView.as_view()

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    
    # Homepage
    path("", include("homepage.urls")),
    
    # Explicit password reset URLs
    path("accounts/password_reset/", 
         auth_views.PasswordResetView.as_view(template_name="registration/password_reset.html"),
         name="password_reset"),
    path("accounts/password_reset/done/",
         auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
         name="password_reset_done"),
    path("accounts/reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"),
         name="password_reset_confirm"),
    path("accounts/reset/done/",
         auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
         name="password_reset_complete"),
    
    # Other auth URLs
    path("accounts/", include("django.contrib.auth.urls")),
    
    # Registration URLs - Using lazy loading for Docker compatibility
    path("accounts/register/", get_registration_view(), name="django_registration_register"),
    
    # Registration activation URLs - ALL required patterns for django_registration
    path("registration/", include([
        # Activation URL (when user clicks email link)
        path("activate/<str:activation_key>/", get_activation_view(), name="django_registration_activate"),
        
        # Registration complete page (after form submission)
        path("complete/", 
             TemplateView.as_view(template_name='django_registration/registration_complete.html'),
             name="django_registration_complete"),
        
        # Activation complete page (after email activation)
        path("activation-complete/",
             TemplateView.as_view(template_name='django_registration/activation_complete.html'),
             name="django_registration_activation_complete"),
        
        # Closed registration page (if needed)
        path("closed/",
             TemplateView.as_view(template_name='django_registration/registration_closed.html'),
             name="django_registration_disallowed"),
    ])),
    
    # App URLs
    path("projects/", include("projects.urls")),
    path("users/", include("users.urls"))
]

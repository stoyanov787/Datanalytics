"""
URL configuration for datanalytics project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django_registration.backends.activation.views import RegistrationView
from users.forms import CustomUserForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('homepage.urls')),
    
    # Explicit password reset URLs
    path('accounts/password_reset/', 
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'),
         name='password_reset'),
    path('accounts/password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('accounts/reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),
         
    # Other auth URLs
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Registration URLs
    path('accounts/register/',
        RegistrationView.as_view(
            form_class=CustomUserForm,
        ),
        name='django_registration_register',
    ),
    path('registration/', include('django_registration.backends.activation.urls')),
    
    # App URLs
    path('projects/', include('projects.urls')),
    path('users/', include('users.urls'))
]

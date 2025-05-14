"""Views for user management"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserProfileForm

@login_required
def profile(request: HttpRequest) -> HttpResponse:
    """View for user profile management.
    
    :param request: The HTTP request object.
    :type request: HttpRequest
    :return: Rendered profile page.
    :rtype: HttpResponse
    """
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, "users/profile.html", {"form": form})

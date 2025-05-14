"""Views for the homepage app."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

def index(request: HttpRequest) -> HttpResponse:
    """Render the homepage."""
    return render(request, "home/index.html")

def about_us(request: HttpRequest) -> HttpResponse:
    """Render the about us page."""
    return render(request, "home/about_us.html")

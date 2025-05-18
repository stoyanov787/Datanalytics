"""Middleware for handling HTTP method overrides in Django."""

from typing import Callable
from django.http import HttpRequest, HttpResponse

class MethodOverrideMiddleware:
    """Middleware to override HTTP methods based on a hidden _method field."""
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize the middleware with the get_response callable."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request and override the HTTP method if necessary."""
        if request.method == "POST" and "_method" in request.POST:
            request.method = request.POST["_method"].upper()
        return self.get_response(request)
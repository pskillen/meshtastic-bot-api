"""Django middleware for authentication and request logging."""

import logging

from django.conf import settings
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


class LoginRequiredMiddleware:
    """Middleware to require authentication for all non-API routes."""

    def __init__(self, get_response):
        """Initialize the middleware with the next middleware in the chain."""
        self.get_response = get_response

    def __call__(self, request):
        """Process the request and redirect to login if not authenticated."""
        path = request.path

        if path.startswith(settings.LOGIN_URL):
            return self.get_response(request)
        if path == "/auth/api-auth-token/":
            return self.get_response(request)
        if path.startswith("/api/"):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={path}")
        return self.get_response(request)


class LogBadRequestMiddleware:
    """Middleware to log details of bad requests to the raw packet endpoint."""

    def __init__(self, get_response):
        """Initialize the middleware with the next middleware in the chain."""
        self.get_response = get_response

    def __call__(self, request):
        """Process the request and log details of bad requests to /api/raw-packet."""
        response = self.get_response(request)

        # Log bad requests to /api/raw-packet since these are malformed packets coming from the bot
        if response.status_code == 400 and request.path == "/api/raw-packet":
            logger.error(f"400 Bad Request: {request.path}")
            logger.error(f"Request body: {request.body}")
            logger.error(f"Request headers: {request.headers}")

        return response

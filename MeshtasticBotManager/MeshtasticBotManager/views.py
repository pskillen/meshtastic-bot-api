"""Views for the MeshtasticBotManager app."""

from django.conf import settings

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def status(request):
    """
    Return basic status information including the version.

    This endpoint is public and doesn't require authentication.
    """
    return Response({"status": "ok", "version": settings.VERSION})

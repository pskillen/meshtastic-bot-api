"""
URL configuration for MeshtasticBotManager project.

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
from django.urls import include, path
from django.views.generic import TemplateView

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from MessageViewer.urls import api_router as ui_api_router
from MessageViewer.urls import urlpatterns as message_viewer_urls
from NodeDB.urls import api_router as nodedb_api_router
from PacketLogging.urls import api_router as packets_api_router
from PacketLogging.urls import urlpatterns as packets_urls
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path(
        "",
        TemplateView.as_view(template_name="MessageViewer/home.html.j2"),
        name="home",
    ),
    path("ui/", include(message_viewer_urls)),
    path("admin/", admin.site.urls),
    path(
        "api/",
        include(
            [
                path("nodes/", include(nodedb_api_router.urls)),
                path("packets/", include(packets_api_router.urls)),
                path("raw-packet/", include(packets_urls)),
                path("ui/", include(ui_api_router.urls)),
            ]
        ),
    ),
    path(
        "auth/",
        include(
            [
                path("api/", include("rest_framework.urls", namespace="rest_framework")),
                path("api-auth-token/", obtain_auth_token),
            ]
        ),
    ),
    # API Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

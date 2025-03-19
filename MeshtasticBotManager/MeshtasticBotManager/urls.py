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
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

import NodeDB.views
import PacketLogging.views
from MessageViewer.urls import urlpatterns as message_viewer_urls

api_router = routers.DefaultRouter()
api_router.register(r'nodes', NodeDB.views.MeshNodeViewSet)
api_router.register(r'packets/raw', PacketLogging.views.RawPacketViewSet)
api_router.register(r'packets/message', PacketLogging.views.MessagePacketViewSet)
api_router.register(r'packets/position', PacketLogging.views.PositionPacketViewSet)
api_router.register(r'packets/nodeinfo', PacketLogging.views.NodeInfoPacketViewSet)
api_router.register(r'packets/encrypted', PacketLogging.views.EncryptedPacketViewSet)
api_router.register(r'packets/telemetry', PacketLogging.views.TelemetryPacketViewSet)

urlpatterns = [
    path("", TemplateView.as_view(template_name="MeshtasticBotManager/home.html.j2"), name="home"),
    path("admin/", admin.site.urls),
    path('api/', include(api_router.urls)),
    path('api/raw-packet/', PacketLogging.views.PacketCreateView.as_view(), name='packet-create'),
    path('auth/', include([
        path('api/', include('rest_framework.urls', namespace='rest_framework')),
        path('api-auth-token/', obtain_auth_token),
    ])),
    path('messages/', include(message_viewer_urls)),
]

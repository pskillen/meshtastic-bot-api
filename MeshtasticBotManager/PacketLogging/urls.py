from django.urls import path

import PacketLogging.views
from rest_framework import routers

api_router = routers.DefaultRouter()
api_router.register(r"raw", PacketLogging.views.RawPacketViewSet)
api_router.register(r"message", PacketLogging.views.MessagePacketViewSet)
api_router.register(r"position", PacketLogging.views.PositionPacketViewSet)
api_router.register(r"nodeinfo", PacketLogging.views.NodeInfoPacketViewSet)
api_router.register(r"encrypted", PacketLogging.views.EncryptedPacketViewSet)
api_router.register(r"telemetry", PacketLogging.views.TelemetryPacketViewSet)

urlpatterns = [
    path("", PacketLogging.views.PacketCreateView.as_view(), name='packet-create'),
]

"""Views for managing mesh network packets through the REST API."""

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from typing_extensions import deprecated

from .models import EncryptedPacket, MessagePacket, NodeInfoPacket, PositionPacket, RawPacket, TelemetryPacket
from .serializers import (
    EncryptedPacketSerializer,
    IncomingDeviceMetricsPacketSerializer,
    IncomingEncryptedPacketSerializer,
    IncomingEnvironmentMetricsPacketSerializer,
    IncomingLocalStatsPacketSerializer,
    IncomingMessagePacketSerializer,
    IncomingMessageReplyPacketSerializer,
    IncomingNodeInfoPacketSerializer,
    IncomingPositionPacketSerializer,
    IncomingRawPacketSerializer,
    MessagePacketSerializer,
    NodeInfoPacketSerializer,
    PositionPacketSerializer,
    RawPacketSerializer,
    TelemetryPacketSerializer,
)


class RawPacketViewSet(viewsets.ModelViewSet):
    """ViewSet for managing raw mesh network packets."""

    queryset = RawPacket.objects.all()
    serializer_class = RawPacketSerializer


class EncryptedPacketViewSet(viewsets.ModelViewSet):
    """ViewSet for managing encrypted mesh network packets."""

    queryset = EncryptedPacket.objects.all()
    serializer_class = EncryptedPacketSerializer


class MessagePacketViewSet(viewsets.ModelViewSet):
    """ViewSet for managing text message packets."""

    queryset = MessagePacket.objects.all()
    serializer_class = MessagePacketSerializer


class PositionPacketViewSet(viewsets.ModelViewSet):
    """ViewSet for managing node position data packets."""

    queryset = PositionPacket.objects.all()
    serializer_class = PositionPacketSerializer


class NodeInfoPacketViewSet(viewsets.ModelViewSet):
    """ViewSet for managing node information packets."""

    queryset = NodeInfoPacket.objects.all()
    serializer_class = NodeInfoPacketSerializer


@deprecated("Use DeviceMetricsPacket or LocalStatsPacket instead")
class TelemetryPacketViewSet(viewsets.ModelViewSet):
    """ViewSet for managing device telemetry packets (deprecated)."""

    queryset = TelemetryPacket.objects.all()
    serializer_class = TelemetryPacketSerializer


class PacketCreateView(APIView):
    """View for creating new mesh network packets based on their type."""

    def _get_serializer(self, request):
        """Determine the appropriate serializer based on the packet type and data.

        Args:
            request: The HTTP request containing the packet data.

        Returns:
            tuple: A tuple containing (serializer, error) where error is None if successful.
        """
        if "encrypted" in request.data and request.data["encrypted"] is not None:
            return IncomingEncryptedPacketSerializer(data=request.data), None

        decoded_data = request.data.get("decoded", {})
        portnum = decoded_data.get("portnum", "unknown")

        if portnum == "TEXT_MESSAGE_APP":
            if decoded_data.get("replyId", None):
                return IncomingMessageReplyPacketSerializer(data=request.data), None
            return IncomingMessagePacketSerializer(data=request.data), None

        if portnum == "POSITION_APP":
            return IncomingPositionPacketSerializer(data=request.data), None

        if portnum == "NODEINFO_APP":
            return IncomingNodeInfoPacketSerializer(data=request.data), None

        if portnum == "TELEMETRY_APP":
            telemetry_data = decoded_data.get("telemetry", None)
            if not telemetry_data:
                return None, {"error": "Telemetry packet with no telemetry data"}

            if telemetry_data.get("deviceMetrics", None):
                return IncomingDeviceMetricsPacketSerializer(data=request.data), None
            if telemetry_data.get("localStats", None):
                return IncomingLocalStatsPacketSerializer(data=request.data), None
            if telemetry_data.get("environmentMetrics", None):
                return (
                    IncomingEnvironmentMetricsPacketSerializer(data=request.data),
                    None,
                )

            return None, {"error": "Telemetry packet with unknown telemetry data"}

        return IncomingRawPacketSerializer(data=request.data), None

    def post(self, request, *args, **kwargs):
        """Handle POST requests to create new packets.

        Args:
            request: The HTTP request containing the packet data.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: A Response object containing the created packet data or error message.
        """
        serializer, error = self._get_serializer(request)
        if error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

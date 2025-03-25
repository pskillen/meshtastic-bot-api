from typing_extensions import deprecated

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NodeInfoPacket, PositionPacket, MessagePacket, EncryptedPacket, RawPacket, TelemetryPacket
from .serializers import NodeInfoPacketSerializer, PositionPacketSerializer, MessagePacketSerializer, \
    EncryptedPacketSerializer, RawPacketSerializer, IncomingEncryptedPacketSerializer, IncomingMessagePacketSerializer, \
    IncomingPositionPacketSerializer, IncomingNodeInfoPacketSerializer, IncomingRawPacketSerializer, \
    TelemetryPacketSerializer, IncomingMessageReplyPacketSerializer, \
    IncomingDeviceMetricsPacketSerializer, IncomingLocalStatsPacketSerializer


class RawPacketViewSet(viewsets.ModelViewSet):
    queryset = RawPacket.objects.all()
    serializer_class = RawPacketSerializer


class EncryptedPacketViewSet(viewsets.ModelViewSet):
    queryset = EncryptedPacket.objects.all()
    serializer_class = EncryptedPacketSerializer


class MessagePacketViewSet(viewsets.ModelViewSet):
    queryset = MessagePacket.objects.all()
    serializer_class = MessagePacketSerializer


class PositionPacketViewSet(viewsets.ModelViewSet):
    queryset = PositionPacket.objects.all()
    serializer_class = PositionPacketSerializer


class NodeInfoPacketViewSet(viewsets.ModelViewSet):
    queryset = NodeInfoPacket.objects.all()
    serializer_class = NodeInfoPacketSerializer


@deprecated("Use DeviceMetricsPacket or LocalStatsPacket instead")
class TelemetryPacketViewSet(viewsets.ModelViewSet):
    queryset = TelemetryPacket.objects.all()
    serializer_class = TelemetryPacketSerializer


class PacketCreateView(APIView):
    def post(self, request, *args, **kwargs):
        # Todo: parse any packet type to an appropriate subclass of RawPacket, or fail and attempt to parse to RawPacket

        if request.data.get('encrypted'):
            serializer = IncomingEncryptedPacketSerializer(data=request.data)

        elif request.data.get('decoded'):
            decoded_data = request.data['decoded']
            portnum = decoded_data.get('portnum', 'unknown')

            if portnum == 'TEXT_MESSAGE_APP':
                # is this a message reply?
                if decoded_data.get('replyId', None):
                    serializer = IncomingMessageReplyPacketSerializer(data=request.data)
                else:
                    serializer = IncomingMessagePacketSerializer(data=request.data)
            elif portnum == 'POSITION_APP':
                serializer = IncomingPositionPacketSerializer(data=request.data)
            elif portnum == 'NODEINFO_APP':
                serializer = IncomingNodeInfoPacketSerializer(data=request.data)
            elif portnum == 'TELEMETRY_APP':
                telemetry_data = decoded_data.get('telemetry', None)
                if not telemetry_data:
                    return Response({'error': 'Invalid packet type'}, status=status.HTTP_400_BAD_REQUEST)

                if telemetry_data.get('deviceMetrics', None):
                    serializer = IncomingDeviceMetricsPacketSerializer(data=request.data)
                elif telemetry_data.get('localStats', None):
                    serializer = IncomingLocalStatsPacketSerializer(data=request.data)
                else:
                    return Response({'error': 'Invalid packet type'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer = IncomingRawPacketSerializer(data=request.data)
        else:
            return Response({'error': 'Invalid packet type'}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

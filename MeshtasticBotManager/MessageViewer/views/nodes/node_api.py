import dateutil.parser
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from NodeDB.models import MeshNode, DeviceMetrics
from PacketLogging.models import DeviceMetricsPacket
from common.mesh_node_helpers import meshtastic_id_to_hex


class NodeViewSet(viewsets.GenericViewSet):
    queryset = MeshNode.objects.all()

    def retrieve(self, request, pk=None):
        node = get_object_or_404(MeshNode, pk=pk)

        # Get the latest DeviceMetrics packet
        latest_device_metrics = DeviceMetrics.objects \
            .filter(node=node).order_by('-logged_time').first()

        # Get the latest DeviceMetricsPacket
        latest_device_metrics_packet = DeviceMetricsPacket.objects \
            .filter(from_int=node.id).order_by('-time').first()

        # Enrich the node data
        node_data = {
            'id': node.id,
            'node_id': meshtastic_id_to_hex(node.id),
            'short_name': node.user.short_name,
            'long_name': node.user.long_name,
            # 'last_heard': pretty_print_last_heard(node.last_heard),
            'hardware_model': node.hw_model,
            'meshtastic_version': '---',
            'latest_device_metrics': latest_device_metrics,
            'latest_device_metrics_packet': latest_device_metrics_packet,
        }

        return Response(node_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def device_metrics(self, request, pk=None):
        start_date = request.query_params.get('startDate')
        end_date = request.query_params.get('endDate')

        node = get_object_or_404(MeshNode, pk=pk)

        # Parse the dates if provided
        if start_date:
            try:
                start_date = dateutil.parser.isoparse(start_date)
            except ValueError:
                return Response({'error': 'Invalid startDate format'}, status=status.HTTP_400_BAD_REQUEST)
        if end_date:
            try:
                end_date = dateutil.parser.isoparse(end_date)
            except ValueError:
                return Response({'error': 'Invalid endDate format'}, status=status.HTTP_400_BAD_REQUEST)

        # Get battery history from DeviceMetrics
        device_metrics = DeviceMetrics.objects.filter(node=node)
        if start_date:
            device_metrics = device_metrics.filter(logged_time__gte=start_date)
        if end_date:
            device_metrics = device_metrics.filter(logged_time__lte=end_date)
        device_metrics = device_metrics.order_by('logged_time')
        battery_history = [
            {
                'time': metric.logged_time,
                'battery_level': metric.battery_level,
                'voltage': metric.voltage,
                'chUtil': metric.channel_utilization,
                'airUtil': metric.air_util_tx,
                'uptime': metric.uptime_seconds,
            }
            for metric in device_metrics
        ]

        # Get battery history from DeviceMetricsPacket
        device_metrics_packets = DeviceMetricsPacket.objects.filter(from_int=node.id)
        if start_date:
            device_metrics_packets = device_metrics_packets.filter(time__gte=start_date)
        if end_date:
            device_metrics_packets = device_metrics_packets.filter(time__lte=end_date)
        device_metrics_packets = device_metrics_packets.order_by('time')
        battery_history += [
            {
                'time': packet.time,
                'battery_level': packet.batteryLevel,
                'voltage': packet.voltage,
                'chUtil': packet.channelUtilization,
                'airUtil': packet.airUtilTx,
                'uptime': packet.uptimeSeconds,
            }
            for packet in device_metrics_packets
        ]

        # Combine the data
        battery_history = sorted(battery_history, key=lambda x: x['time'])

        return Response(battery_history, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([], status=status.HTTP_200_OK)

        # Search in id_str, short_name, and long_name
        nodes = MeshNode.objects.filter(
            id_str__icontains=query
        ) | MeshNode.objects.filter(
            user__short_name__icontains=query
        ) | MeshNode.objects.filter(
            user__long_name__icontains=query
        )

        results = [{
            'id': node.id,
            'node_id': meshtastic_id_to_hex(node.id),
            'short_name': node.user.short_name,
            'long_name': node.user.long_name,
        } for node in nodes]

        return Response(results, status=status.HTTP_200_OK)

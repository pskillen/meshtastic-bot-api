"""API endpoints for managing mesh nodes.

This module provides API endpoints for retrieving information about mesh nodes,
including their device metrics, position history, and other details.
"""

from django.shortcuts import get_object_or_404

import dateutil.parser
from common.mesh_node_helpers import meshtastic_id_to_hex
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from NodeDB.models import DeviceMetrics, MeshNode, Position
from PacketLogging.models import DeviceMetricsPacket, RawPacket
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


@extend_schema_view(
    list=extend_schema(
        summary="List all nodes",
        description="Returns a list of all mesh nodes in the network with their basic information.",
        responses={200: "List of nodes"},
        tags=["Nodes"],
    ),
    retrieve=extend_schema(
        summary="Get node details",
        description="Retrieve detailed information about a specific node by ID.",
        responses={200: "Node details", 404: "Node not found"},
        tags=["Nodes"],
    ),
    device_metrics=extend_schema(
        summary="Get node device metrics",
        description="Get device metrics (battery, voltage, etc.) for a specific node over time.",
        parameters=[
            OpenApiParameter(
                name="startDate", description="Start date for metrics (ISO format)", required=False, type=str
            ),
            OpenApiParameter(name="endDate", description="End date for metrics (ISO format)", required=False, type=str),
        ],
        responses={200: "List of device metrics", 400: "Bad request - invalid date format", 404: "Node not found"},
        tags=["Nodes"],
    ),
    positions=extend_schema(
        summary="Get node position history",
        description="Get position history for a specific node over time.",
        parameters=[
            OpenApiParameter(
                name="startDate", description="Start date for position history (ISO format)", required=False, type=str
            ),
            OpenApiParameter(
                name="endDate", description="End date for position history (ISO format)", required=False, type=str
            ),
        ],
        responses={200: "List of positions", 400: "Bad request - invalid date format", 404: "Node not found"},
        tags=["Nodes"],
    ),
    search=extend_schema(
        summary="Search for nodes",
        description="Search for nodes by ID or name.",
        parameters=[
            OpenApiParameter(name="q", description="Search query", required=True, type=str),
        ],
        responses={200: "List of matching nodes"},
        tags=["Nodes"],
    ),
)
class NodeViewSet(viewsets.GenericViewSet):
    """ViewSet for managing mesh nodes.

    This ViewSet provides endpoints for retrieving information about mesh nodes,
    including their device metrics, position history, and other details.
    """

    queryset = MeshNode.objects.all()

    def list(self, request):
        """List all mesh nodes."""
        nodes = MeshNode.objects.all()
        node_list = [self._node_to_json(node) for node in nodes]
        return Response(node_list, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """Retrieve a specific mesh node by ID."""
        node = get_object_or_404(MeshNode, pk=pk)
        return Response(self._node_to_json(node), status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def device_metrics(self, request, pk=None):
        """Get device metrics for a specific node."""
        start_date = request.query_params.get("startDate")
        end_date = request.query_params.get("endDate")

        node = get_object_or_404(MeshNode, pk=pk)

        # Parse the dates if provided
        if start_date:
            try:
                start_date = dateutil.parser.isoparse(start_date)
            except ValueError:
                return Response(
                    {"error": "Invalid startDate format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if end_date:
            try:
                end_date = dateutil.parser.isoparse(end_date)
            except ValueError:
                return Response(
                    {"error": "Invalid endDate format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Get metrics from both sources
        device_metrics = DeviceMetrics.objects.filter(node=node)
        if start_date:
            device_metrics = device_metrics.filter(logged_time__gte=start_date)
        if end_date:
            device_metrics = device_metrics.filter(logged_time__lte=end_date)
        device_metrics = device_metrics.order_by("logged_time")

        device_metrics_packets = DeviceMetricsPacket.objects.filter(from_int=node.id)
        if start_date:
            device_metrics_packets = device_metrics_packets.filter(time__gte=start_date)
        if end_date:
            device_metrics_packets = device_metrics_packets.filter(time__lte=end_date)
        device_metrics_packets = device_metrics_packets.order_by("time")

        # Combine and normalize all metrics
        metrics_data = []
        metrics_data.extend(self._normalize_device_metrics(metric) for metric in device_metrics)
        metrics_data.extend(self._normalize_device_metrics(packet) for packet in device_metrics_packets)

        # Sort by time
        metrics_data = sorted(metrics_data, key=lambda x: x["time"])

        return Response(metrics_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def positions(self, request, pk=None):
        """Get position history for a specific node."""
        start_date = request.query_params.get("startDate")
        end_date = request.query_params.get("endDate")

        node = get_object_or_404(MeshNode, pk=pk)

        # Parse the dates if provided
        if start_date:
            try:
                start_date = dateutil.parser.isoparse(start_date)
            except ValueError:
                return Response(
                    {"error": "Invalid startDate format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if end_date:
            try:
                end_date = dateutil.parser.isoparse(end_date)
            except ValueError:
                return Response(
                    {"error": "Invalid endDate format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Get position history
        positions = Position.objects.filter(node=node)
        if start_date:
            positions = positions.filter(logged_time__gte=start_date)
        if end_date:
            positions = positions.filter(logged_time__lte=end_date)
        positions = positions.order_by("logged_time")

        position_history = [
            {
                "time": position.logged_time,
                "reported_time": position.reported_time,
                "latitude": position.latitude,
                "longitude": position.longitude,
                "altitude": position.altitude,
                "location_source": position.location_source,
            }
            for position in positions
        ]

        return Response(position_history, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def search(self, request):
        """Search for nodes by ID or name."""
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response([], status=status.HTTP_200_OK)

        # Search in id_str, short_name, and long_name
        nodes = (
            MeshNode.objects.filter(id_str__icontains=query)
            | MeshNode.objects.filter(user__short_name__icontains=query)
            | MeshNode.objects.filter(user__long_name__icontains=query)
        )

        results = [
            {
                "id": node.id,
                "node_id": meshtastic_id_to_hex(node.id),
                "short_name": node.user.short_name,
                "long_name": node.user.long_name,
            }
            for node in nodes
        ]

        return Response(results, status=status.HTTP_200_OK)

    def _normalize_device_metrics(self, metrics):
        """Convert either DeviceMetrics or DeviceMetricsPacket to a normalized format."""
        if isinstance(metrics, DeviceMetrics):
            return {
                "time": metrics.logged_time,
                "battery_level": metrics.battery_level,
                "voltage": metrics.voltage,
                "chUtil": metrics.channel_utilization,
                "airUtil": metrics.air_util_tx,
                "uptime": metrics.uptime_seconds,
            }
        elif isinstance(metrics, DeviceMetricsPacket):
            return {
                "time": metrics.time,
                "battery_level": metrics.batteryLevel,
                "voltage": metrics.voltage,
                "chUtil": metrics.channelUtilization,
                "airUtil": metrics.airUtilTx,
                "uptime": metrics.uptimeSeconds,
            }
        return None

    def _node_to_json(self, node):
        """Convert a node to its JSON representation."""
        # Get the latest DeviceMetrics packet
        latest_device_metrics = DeviceMetrics.objects.filter(node=node).order_by("-logged_time").first()

        # Get the latest DeviceMetricsPacket
        latest_device_metrics_packet = DeviceMetricsPacket.objects.filter(from_int=node.id).order_by("-time").first()

        # Get the latest RawPacket for last_heard
        latest_raw_packet = RawPacket.objects.filter(from_int=node.id).order_by("-rx_time").first()

        # Get the latest position
        latest_position = Position.objects.filter(node=node).order_by("-logged_time").first()

        # Get the most recent device metrics from either source
        latest_metrics = None
        if latest_device_metrics and latest_device_metrics_packet:
            latest_metrics = (
                latest_device_metrics
                if latest_device_metrics.logged_time > latest_device_metrics_packet.time
                else latest_device_metrics_packet
            )
        elif latest_device_metrics:
            latest_metrics = latest_device_metrics
        elif latest_device_metrics_packet:
            latest_metrics = latest_device_metrics_packet

        return {
            "id": node.id,
            "node_id": meshtastic_id_to_hex(node.id),
            "short_name": node.user.short_name,
            "long_name": node.user.long_name,
            "last_heard": latest_raw_packet.rx_time if latest_raw_packet else None,
            "hardware_model": node.hw_model,
            "meshtastic_version": "---",
            "latest_device_metrics": (self._normalize_device_metrics(latest_metrics) if latest_metrics else None),
            "last_position": (
                {
                    "time": latest_position.logged_time,
                    "reported_time": latest_position.reported_time,
                    "latitude": latest_position.latitude,
                    "longitude": latest_position.longitude,
                    "altitude": latest_position.altitude,
                    "location_source": latest_position.location_source,
                }
                if latest_position
                else None
            ),
        }

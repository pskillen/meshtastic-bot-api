"""View for displaying detailed information about a mesh node."""

from datetime import datetime, timedelta

from django.db.models import OuterRef, Subquery
from django.views.generic import DetailView

from common.mesh_node_helpers import meshtastic_id_to_hex, pretty_print_last_heard
from NodeDB.models import DeviceMetrics, MeshNode, Position
from PacketLogging.models import DeviceMetricsPacket, LocalStatsPacket, MessagePacket, RawPacket


class NodeDetailView(DetailView):
    """View for displaying detailed information about a specific mesh node."""

    model = MeshNode
    template_name = "MessageViewer/nodes/node.html.j2"
    context_object_name = "node"

    def get_queryset(self):
        """Get the queryset for the view, annotating nodes with their last heard time."""
        # Subquery to get the most recent RawPacket for the node
        latest_packet = RawPacket.objects.filter(from_int=OuterRef("pk")).order_by("-rx_time").values("rx_time")[:1]

        return MeshNode.objects.annotate(last_heard=Subquery(latest_packet.values("rx_time")[:1]))

    def get_context_data(self, **kwargs):
        """Get additional context data for the template, including recent messages, positions, and metrics."""
        context = super().get_context_data(**kwargs)
        node = self.get_object()

        # Get recent messages
        recent_messages_from = MessagePacket.objects.filter(from_int=node.id).order_by("-rx_time")[:10]
        recent_messages_to = MessagePacket.objects.filter(to_int=node.id).order_by("-rx_time")[:10]

        # Get recent positions
        recent_positions = Position.objects.filter(node=node).order_by("-logged_time")[:10]

        # Get recent packets
        recent_packets = RawPacket.objects.filter(from_int=node.id).order_by("-rx_time")[:10]

        # Get device metrics for past 7 days
        metrics_time_start = datetime.now() - timedelta(days=7)
        device_metrics = DeviceMetrics.objects.filter(node=node, logged_time__gte=metrics_time_start).order_by(
            "-logged_time"
        )

        device_metrics_packets = DeviceMetricsPacket.objects.filter(
            from_int=node.id, time__gte=metrics_time_start
        ).order_by("-time")
        local_stats_packets = LocalStatsPacket.objects.filter(from_int=node.id, time__gte=metrics_time_start).order_by(
            "-time"
        )

        context.update(
            {
                "node": node,
                "node_id": meshtastic_id_to_hex(node.id),
                "short_name": node.user.short_name,
                "long_name": node.user.long_name,
                "last_heard": pretty_print_last_heard(node.last_heard),
                "hardware_model": node.hw_model,
                "meshtastic_version": "---",
                "recent_messages_from": recent_messages_from,
                "recent_messages_to": recent_messages_to,
                "recent_positions": recent_positions,
                "recent_packets": recent_packets,
                "device_metrics": device_metrics,
                "device_metrics_packets": device_metrics_packets,
                "local_stats_packets": local_stats_packets,
            }
        )
        return context

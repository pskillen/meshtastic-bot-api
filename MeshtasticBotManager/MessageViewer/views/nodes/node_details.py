from django.db.models import OuterRef, Subquery
from django.views.generic import DetailView

from NodeDB.models import MeshNode, Position, DeviceMetrics
from PacketLogging.models import RawPacket, MessagePacket
from common.mesh_node_helpers import meshtastic_id_to_hex, pretty_print_last_heard


class NodeDetailView(DetailView):
    model = MeshNode
    template_name = 'MessageViewer/nodes/node.html.j2'
    context_object_name = 'node'

    def get_queryset(self):
        # Subquery to get the most recent RawPacket for the node
        latest_packet = RawPacket.objects.filter(
            from_int=OuterRef('pk')
        ).order_by('-rx_time').values('rx_time')[:1]

        return MeshNode.objects.annotate(
            last_heard=Subquery(latest_packet.values('rx_time')[:1])
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        node = self.get_object()

        # Get recent messages
        recent_messages_from = MessagePacket.objects.filter(from_int=node.id).order_by('-rx_time')[:10]
        recent_messages_to = MessagePacket.objects.filter(to_int=node.id).order_by('-rx_time')[:10]

        # Get recent positions
        recent_positions = Position.objects.filter(node=node).order_by('-logged_time')[:10]

        # Get recent packets
        recent_packets = RawPacket.objects.filter(from_int=node.id).order_by('-rx_time')[:10]

        # Get device metrics
        device_metrics = DeviceMetrics.objects.filter(node=node).order_by('-logged_time')[:1].first()

        context.update({
            'node': node,
            'node_id': meshtastic_id_to_hex(node.id),
            'short_name': node.user.short_name,
            'long_name': node.user.long_name,
            'last_heard': pretty_print_last_heard(node.last_heard),
            'hardware_model': node.hw_model,
            'meshtastic_version': '---',
            'recent_messages_from': recent_messages_from,
            'recent_messages_to': recent_messages_to,
            'recent_positions': recent_positions,
            'recent_packets': recent_packets,
            'device_metrics': device_metrics,
        })
        return context

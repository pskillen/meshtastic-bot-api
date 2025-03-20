from django.db.models import OuterRef, Subquery
from django.views.generic import TemplateView

from NodeDB.models import MeshNode, Position, DeviceMetrics
from PacketLogging.models import RawPacket
from common.mesh_node_helpers import meshtastic_id_to_hex, pretty_print_last_heard


class NodeListView(TemplateView):
    template_name = 'MessageViewer/nodes/node_list.html.j2'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Subquery to get the most recent Position for each node
        latest_position = Position.objects.filter(
            node=OuterRef('pk')
        ).order_by('-logged_time').values('latitude', 'longitude', 'logged_time')[:1]

        # Subquery to get the most recent DeviceMetrics for each node
        latest_metrics = DeviceMetrics.objects.filter(
            node=OuterRef('pk')
        ).order_by('-logged_time').values('battery_level', 'logged_time')[:1]

        # Subquery to get the most recent RawPacket for each node
        latest_packet = RawPacket.objects.filter(
            from_int=OuterRef('pk')
        ).order_by('-rx_time').values('rx_time')[:1]

        nodes = MeshNode.objects.all().annotate(
            last_position_lat=Subquery(latest_position.values('latitude')[:1]),
            last_position_long=Subquery(latest_position.values('longitude')[:1]),
            last_position_time=Subquery(latest_position.values('logged_time')[:1]),
            battery_voltage=Subquery(latest_metrics.values('voltage')[:1]),
            battery_percent=Subquery(latest_metrics.values('battery_level')[:1]),
            last_metrics_time=Subquery(latest_metrics.values('logged_time')[:1]),
            last_heard=Subquery(latest_packet.values('rx_time')[:1]),
        ).order_by('user__short_name')

        enriched_nodes = []

        for node in nodes:
            enriched_nodes.append({
                'node_id': meshtastic_id_to_hex(node.id),
                'short_name': node.user.short_name,
                'long_name': node.user.long_name,
                'last_heard_ago': pretty_print_last_heard(node.last_heard),
                'last_heard': node.last_heard.strftime('%Y-%m-%d %H:%M:%S') if node.last_heard else None,
                'last_position': f"{node.last_position_lat}, {node.last_position_long}",
                'last_position_time': node.last_position_time.strftime('%Y-%m-%d %H:%M:%S') if node.last_position_time else None,
                'last_position_ago': pretty_print_last_heard(node.last_position_time),
                'battery_voltage': node.battery_voltage,
                'battery_percent': node.battery_percent,
                'hardware_model': node.hw_model,
                'meshtastic_version': '---',  # Assuming this is the version field
            })

        context['nodes'] = enriched_nodes
        return context

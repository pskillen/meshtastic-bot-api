from django.db.models import OuterRef, Subquery
from django.views.generic import TemplateView

from NodeDB.models import MeshNode, Position, DeviceMetrics
from PacketLogging.models import RawPacket
from common.mesh_node_helpers import meshtastic_id_to_hex, pretty_print_last_heard


class NodeListView(TemplateView):
    template_name = 'MessageViewer/nodes/node_list.html.j2'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Subquery to get the most recent Position ID for each node
        latest_position_id = Position.objects.filter(
            node=OuterRef('pk'),
        ).exclude(
            latitude=0,
            longitude=0,
            altitude=0
        ).order_by('-logged_time').values('id')[:1]

        # Subquery to get the most recent DeviceMetrics ID for each node
        latest_metrics_id = DeviceMetrics.objects.filter(
            node=OuterRef('pk')
        ).order_by('-logged_time').values('id')[:1]

        # Subquery to get the most recent RawPacket for each node
        latest_packet = RawPacket.objects.filter(
            from_int=OuterRef('pk')
        ).order_by('-rx_time').values('rx_time')[:1]

        nodes = MeshNode.objects.all().annotate(
            last_position_id=Subquery(latest_position_id),
            last_metrics_id=Subquery(latest_metrics_id),
            last_heard=Subquery(latest_packet.values('rx_time')[:1]),
        ).order_by('user__short_name')

        # Get all the latest Position objects in a single query
        position_ids = [node.last_position_id for node in nodes if node.last_position_id]
        positions = Position.objects.filter(id__in=position_ids)
        position_dict: dict[int, Position] = {position.id: position for position in positions}

        # Get all the latest DeviceMetrics objects in a single query
        metrics_ids = [node.last_metrics_id for node in nodes if node.last_metrics_id]
        metrics = DeviceMetrics.objects.filter(id__in=metrics_ids)
        metrics_dict: dict[int, DeviceMetrics] = {metric.id: metric for metric in metrics}

        enriched_nodes = []

        for node in nodes:
            last_position = position_dict.get(node.last_position_id)
            last_metrics = metrics_dict.get(node.last_metrics_id)
            enriched_nodes.append({
                'node': node,
                'node_id': meshtastic_id_to_hex(node.id),
                'short_name': node.user.short_name,
                'long_name': node.user.long_name,
                'last_heard_ago': pretty_print_last_heard(node.last_heard),
                'last_heard': node.last_heard.strftime('%Y-%m-%d %H:%M:%S') if node.last_heard else None,
                'last_position': last_position,
                'last_position_time': last_position.logged_time.strftime(
                    '%Y-%m-%d %H:%M:%S') if last_position else None,
                'last_position_ago': pretty_print_last_heard(last_position.logged_time) if last_position else None,
                'battery_voltage': last_metrics.voltage if last_metrics else None,
                'battery_percent': last_metrics.battery_level if last_metrics else None,
                'hardware_model': node.hw_model,
                'meshtastic_version': '---',  # Assuming this is the version field
            })

        context['nodes'] = enriched_nodes
        return context

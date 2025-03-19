from django.shortcuts import render

from NodeDB.models import MeshNode
from PacketLogging.models import MessagePacket


def message_history(request):
    selected_node_id = request.GET.get('home-node')

    # Fetch all message packets
    message_packets = MessagePacket.objects.all()
    all_nodes = MeshNode.objects.all()

    # Enrich message packets with MeshNode data
    enriched_messages = []
    for packet in message_packets:
        node = all_nodes.filter(id=packet.from_int).first()
        enriched_messages.append({
            'packet': packet,
            'node': node
        })

    context = {
        'messages': enriched_messages,
        'all_nodes': all_nodes.order_by('user__short_name'),
        'selected_node_id': selected_node_id,
    }

    return render(request, 'MessageViewer/message_history.html.j2', context)

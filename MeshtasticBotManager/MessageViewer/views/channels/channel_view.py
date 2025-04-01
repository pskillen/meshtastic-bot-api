"""View for displaying message history in mesh channels."""

from django.db.models import Prefetch
from django.views.generic import TemplateView

from common.mesh_node_helpers import BROADCAST_ID, meshtastic_id_to_hex
from NodeDB.models import MeshNode
from PacketLogging.models import MessagePacket, MessageReplyPacket


class MessageHistoryView(TemplateView):
    """View for displaying message history in mesh channels, including replies and emoji reactions."""

    template_name = "MessageViewer/channels/message_history.html.j2"

    def get_context_data(self, **kwargs):
        """Get context data for the template, including enriched message data with node info and emoji reactions."""
        context = super().get_context_data(**kwargs)
        selected_node_id = self.request.GET.get("home-node", "")
        channel_num = self.request.GET.get("channel", "-1")
        try:
            channel_num = int(channel_num)
            if channel_num < -1 or channel_num > 8:
                channel_num = -1
        except ValueError:
            channel_num = -1

        # Fetch all nodes
        all_nodes = MeshNode.objects.all()

        # Fetch all message packets
        message_packets = (
            MessagePacket.objects.all() if channel_num == -1 else MessagePacket.objects.filter(channel=channel_num)
        )
        message_packets = message_packets.filter(to_int=BROADCAST_ID).order_by("-rx_time")

        # Prefetch related message reply packets
        response_packets = MessageReplyPacket.objects.filter(
            reply_packet_id__in=[packet.packet_id for packet in message_packets]
        )
        message_packets = message_packets.prefetch_related(
            Prefetch("reply_to", queryset=response_packets, to_attr="replies")
        )

        emoji_reply_ids = [packet.packet_id for packet in response_packets if packet.emoji]

        # Enrich message packets with MeshNode data
        enriched_messages = []
        for packet in message_packets:
            node = all_nodes.filter(id=packet.from_int).first()
            replies = packet.replies

            # if this is a reply emoji, don't add it to the list of replies
            is_emoji_reply = packet.packet_id in emoji_reply_ids
            if is_emoji_reply:
                continue

            # for replies which are emojis, group together into counts
            emojis = {}
            for reply in replies:
                if reply.emoji in emojis:
                    emojis[reply.emoji] += 1
                else:
                    emojis[reply.emoji] = 1

            enriched_messages.append(
                {
                    "packet": packet,
                    "replies": replies,
                    "emojis": emojis,
                    "node": node,
                    "node_id": packet.from_int,
                    "node_id_str": meshtastic_id_to_hex(packet.from_int),
                }
            )

        context.update(
            {
                "messages": enriched_messages,
                "all_nodes": all_nodes.order_by("user__short_name"),
                "selected_node_id": selected_node_id,
                "selected_channel": channel_num,
            }
        )

        return context

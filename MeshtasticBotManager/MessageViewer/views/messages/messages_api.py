"""API endpoints for managing mesh messages."""

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from common.mesh_node_helpers import BROADCAST_ID, meshtastic_id_to_hex
from NodeDB.models import MeshNode
from PacketLogging.models import MessagePacket, MessageReplyPacket
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class MessagesPagination(LimitOffsetPagination):
    """Custom pagination for messages with a maximum limit of 250."""

    default_limit = 100
    max_limit = 250


class MessagesViewSet(viewsets.GenericViewSet):
    """ViewSet for managing mesh messages."""

    queryset = MessagePacket.objects.all()
    pagination_class = MessagesPagination

    def list(self, request):
        """List messages with filtering by channel or node (required)."""
        # Get query parameters
        channel_num = request.query_params.get("channel", "-1")
        node_id = request.query_params.get("node", "")

        try:
            channel_num = int(channel_num)
            if channel_num < -1 or channel_num > 8:
                channel_num = -1
        except ValueError:
            channel_num = -1

        # Enforce that either a valid channel or node filter is provided
        has_valid_channel = channel_num != -1
        has_valid_node = bool(node_id)

        if not has_valid_channel and not has_valid_node:
            return Response(
                {"error": "Either a channel or node filter must be provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch all nodes for enrichment
        all_nodes = MeshNode.objects.all()

        # Fetch message packets with optional filtering
        message_packets = MessagePacket.objects.all()

        # Filter by channel if specified
        if channel_num != -1:
            message_packets = message_packets.filter(channel=channel_num)

        # Filter by node if specified
        if node_id:
            try:
                node_id = int(node_id)
                message_packets = message_packets.filter(from_int=node_id)
            except ValueError:
                pass

        # Only get broadcast messages (to all nodes)
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

            # if this is a reply emoji, don't add it to the list of messages
            is_emoji_reply = packet.packet_id in emoji_reply_ids
            if is_emoji_reply:
                continue

            # for replies which are emojis, group together into counts
            emojis = {}
            for reply in replies:
                if reply.emoji:
                    if reply.emoji in emojis:
                        emojis[reply.emoji] += 1
                    else:
                        emojis[reply.emoji] = 1

            enriched_messages.append(self._message_to_json(packet, node, replies, emojis))

        # Apply pagination to the enriched messages
        paginator = self.pagination_class()
        paginated_messages = paginator.paginate_queryset(enriched_messages, request)

        return paginator.get_paginated_response(paginated_messages)

    def retrieve(self, request, pk=None):
        """Retrieve a specific message by ID."""
        packet = get_object_or_404(MessagePacket, pk=pk)

        # Get the node that sent this message
        node = MeshNode.objects.filter(id=packet.from_int).first()

        # Get replies to this message
        replies = MessageReplyPacket.objects.filter(reply_packet_id=packet.packet_id)

        # Group emoji reactions
        emojis = {}
        for reply in replies:
            if reply.emoji:
                if reply.emoji in emojis:
                    emojis[reply.emoji] += 1
                else:
                    emojis[reply.emoji] = 1

        return Response(self._message_to_json(packet, node, replies, emojis), status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def by_channel(self, request):
        """Get messages for a specific channel."""
        channel_num = request.query_params.get("channel", "-1")

        try:
            channel_num = int(channel_num)
            if channel_num < -1 or channel_num > 8:
                return Response(
                    {"error": "Invalid channel number"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError:
            return Response(
                {"error": "Invalid channel format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reuse the list method with the channel parameter
        request.query_params._mutable = True
        request.query_params["channel"] = str(channel_num)
        request.query_params._mutable = False

        return self.list(request)

    @action(detail=False, methods=["get"])
    def by_node(self, request):
        """Get messages from a specific node."""
        node_id = request.query_params.get("node", "")

        if not node_id:
            return Response(
                {"error": "Node ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reuse the list method with the node parameter
        request.query_params._mutable = True
        request.query_params["node"] = node_id
        request.query_params._mutable = False

        return self.list(request)

    def _message_to_json(self, packet, node, replies, emojis):
        """Convert a message packet to its JSON representation."""
        # Format replies for JSON response
        formatted_replies = []
        for reply in replies:
            if not reply.emoji:  # Only include text replies here
                reply_node = MeshNode.objects.filter(id=reply.from_int).first()
                formatted_replies.append({
                    "id": str(reply.id),
                    "packet_id": reply.packet_id,
                    "message_text": reply.message_text,
                    "rx_time": reply.rx_time,
                    "from_node": {
                        "id": reply.from_int,
                        "node_id": meshtastic_id_to_hex(reply.from_int),
                        "short_name": reply_node.user.short_name if reply_node else "Unknown",
                    }
                })

        # Format emoji reactions
        formatted_emojis = [{"emoji": emoji, "count": count} for emoji, count in emojis.items()]

        return {
            "id": str(packet.id),
            "packet_id": packet.packet_id,
            "message_text": packet.message_text,
            "channel": packet.channel,
            "rx_time": packet.rx_time,
            "from_node": {
                "id": packet.from_int,
                "node_id": meshtastic_id_to_hex(packet.from_int),
                "short_name": node.user.short_name if node else "Unknown",
            },
            "replies": formatted_replies,
            "emojis": formatted_emojis,
        }

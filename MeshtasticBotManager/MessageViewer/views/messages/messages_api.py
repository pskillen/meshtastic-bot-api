"""API endpoints for managing mesh messages.

This module provides API endpoints for retrieving and filtering messages sent over the mesh network.
Messages can be filtered by channel or node, and include information about replies and emoji reactions.

Performance Optimizations:
1. Database indexes on frequently queried fields (packet_id, from_int, to_int, channel, rx_time)
2. Efficient query patterns using select_related and prefetch_related
3. Reduced number of database queries by fetching only needed data
4. Optimized emoji processing with dictionary-based counting
5. Use of sets and dictionaries for O(1) lookups instead of list iterations
"""

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from common.mesh_node_helpers import BROADCAST_ID, meshtastic_id_to_hex
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema, extend_schema_view
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


@extend_schema_view(
    list=extend_schema(
        summary="List messages",
        description="List messages with filtering by channel or node (required). Returns paginated results.",
        parameters=[
            OpenApiParameter(
                name="channel", description="Channel number to filter messages by (0-8)", required=False, type=int
            ),
            OpenApiParameter(name="node", description="Node ID to filter messages by", required=False, type=str),
            OpenApiParameter(
                name="limit", description="Number of messages to return (max 250)", required=False, type=int
            ),
            OpenApiParameter(name="offset", description="Offset for pagination", required=False, type=int),
        ],
        responses={200: "List of messages with pagination metadata", 400: "Bad request - missing required filter"},
        examples=[
            OpenApiExample(
                "Example Response",
                value={
                    "count": 10,
                    "next": "http://example.com/api/ui/messages/?channel=0&limit=10&offset=10",
                    "previous": None,
                    "results": [
                        {
                            "id": "uuid",
                            "packet_id": 12345,
                            "message_text": "Hello world",
                            "channel": 0,
                            "rx_time": "2023-01-01T12:00:00Z",
                            "from_node": {"id": 123456789, "node_id": "!abcdef", "short_name": "Node1"},
                            "replies": [],
                            "emojis": [],
                        }
                    ],
                },
            )
        ],
        tags=["Messages"],
    ),
    retrieve=extend_schema(
        summary="Get message details",
        description="Retrieve a specific message by ID, including replies and emoji reactions.",
        responses={200: "Message details", 404: "Message not found"},
        tags=["Messages"],
    ),
    by_channel=extend_schema(
        summary="Get messages by channel",
        description="Get messages for a specific channel.",
        parameters=[
            OpenApiParameter(name="channel", description="Channel number (0-8)", required=True, type=int),
            OpenApiParameter(
                name="limit", description="Number of messages to return (max 250)", required=False, type=int
            ),
            OpenApiParameter(name="offset", description="Offset for pagination", required=False, type=int),
        ],
        responses={200: "List of messages with pagination metadata", 400: "Bad request - invalid channel"},
        tags=["Messages"],
    ),
    by_node=extend_schema(
        summary="Get messages by node",
        description="Get messages from a specific node.",
        parameters=[
            OpenApiParameter(name="node", description="Node ID", required=True, type=str),
            OpenApiParameter(
                name="limit", description="Number of messages to return (max 250)", required=False, type=int
            ),
            OpenApiParameter(name="offset", description="Offset for pagination", required=False, type=int),
        ],
        responses={200: "List of messages with pagination metadata", 400: "Bad request - missing node ID"},
        tags=["Messages"],
    ),
)
class MessagesViewSet(viewsets.GenericViewSet):
    """ViewSet for managing mesh messages.

    This ViewSet provides endpoints for retrieving and filtering messages sent over the mesh network.
    Messages can be filtered by channel or node, and include information about replies and emoji reactions.
    """

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

        # Start with a filtered query instead of fetching all messages
        message_packets = MessagePacket.objects.filter(to_int=BROADCAST_ID)

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

        # Order by rx_time
        message_packets = message_packets.order_by("-rx_time")

        # Create a set of from_int values for efficient node lookup
        from_int_values = set(message_packets.values_list("from_int", flat=True))

        # Fetch only the nodes we need
        nodes_dict = {node.id: node for node in MeshNode.objects.filter(id__in=from_int_values).select_related("user")}

        # Get packet_ids for emoji filtering
        packet_ids = list(message_packets.values_list("packet_id", flat=True))

        # Prefetch related message reply packets more efficiently
        message_packets = message_packets.prefetch_related(
            Prefetch(
                "reply_to",
                queryset=MessageReplyPacket.objects.filter(reply_packet_id__in=packet_ids),
                to_attr="replies",
            )
        )

        # Get emoji reply packet_ids for filtering
        emoji_reply_ids = set(
            MessageReplyPacket.objects.filter(reply_packet_id__in=packet_ids, emoji__isnull=False).values_list(
                "packet_id", flat=True
            )
        )

        # Enrich message packets with MeshNode data
        enriched_messages = []
        for packet in message_packets:
            # Skip emoji replies
            if packet.packet_id in emoji_reply_ids:
                continue

            # Get node from dictionary instead of querying
            node = nodes_dict.get(packet.from_int)
            replies = getattr(packet, "replies", [])

            # Group emoji reactions more efficiently
            emojis = {}
            for reply in replies:
                if reply.emoji:
                    emojis[reply.emoji] = emojis.get(reply.emoji, 0) + 1

            enriched_messages.append(self._message_to_json(packet, node, replies, emojis))

        # Apply pagination to the enriched messages
        paginator = self.pagination_class()
        paginated_messages = paginator.paginate_queryset(enriched_messages, request)

        return paginator.get_paginated_response(paginated_messages)

    def retrieve(self, request, pk=None):
        """Retrieve a specific message by ID."""
        # Get the message with a single query, using select_related to get the node info
        packet = get_object_or_404(MessagePacket, pk=pk)

        # Get the node that sent this message, using select_related to reduce queries
        node = MeshNode.objects.filter(id=packet.from_int).select_related("user").first()

        # Get replies to this message efficiently
        replies = MessageReplyPacket.objects.filter(reply_packet_id=packet.packet_id)

        # Group emoji reactions more efficiently
        emojis = {}
        for reply in replies:
            if reply.emoji:
                emojis[reply.emoji] = emojis.get(reply.emoji, 0) + 1

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
        # Get all unique node IDs from replies to fetch them in a single query
        reply_node_ids = {reply.from_int for reply in replies if not reply.emoji}

        # Fetch all reply nodes in a single query if there are any
        reply_nodes = {}
        if reply_node_ids:
            reply_nodes = {
                node.id: node for node in MeshNode.objects.filter(id__in=reply_node_ids).select_related("user")
            }

        # Format replies for JSON response
        formatted_replies = []
        for reply in replies:
            if not reply.emoji:  # Only include text replies here
                reply_node = reply_nodes.get(reply.from_int)
                formatted_replies.append(
                    {
                        "id": str(reply.id),
                        "packet_id": reply.packet_id,
                        "message_text": reply.message_text,
                        "rx_time": reply.rx_time,
                        "from_node": {
                            "id": reply.from_int,
                            "node_id": meshtastic_id_to_hex(reply.from_int),
                            "short_name": (
                                reply_node.user.short_name if reply_node and hasattr(reply_node, "user") else "Unknown"
                            ),
                        },
                    }
                )

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
                "short_name": node.user.short_name if node and hasattr(node, "user") else "Unknown",
            },
            "replies": formatted_replies,
            "emojis": formatted_emojis,
        }

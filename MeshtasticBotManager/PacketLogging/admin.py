"""Admin interface configuration for the PacketLogging app."""

from django.contrib import admin

from .models import EncryptedPacket, MessagePacket, NodeInfoPacket, PositionPacket, RawPacket, TelemetryPacket


@admin.register(RawPacket)
class RawPacketAdmin(admin.ModelAdmin):
    """Admin interface for managing raw mesh network packets."""

    list_display = ("id", "packet_id", "from_str", "to_str", "channel", "rx_time")


@admin.register(EncryptedPacket)
class EncryptedPacketAdmin(admin.ModelAdmin):
    """Admin interface for managing encrypted mesh network packets."""

    list_display = ("id", "packet_id", "from_str", "to_str", "channel", "rx_time")


@admin.register(MessagePacket)
class MessagePacketAdmin(admin.ModelAdmin):
    """Admin interface for managing text message packets."""

    list_display = (
        "id",
        "packet_id",
        "from_str",
        "to_str",
        "channel",
        "rx_time",
        "message_text",
    )


@admin.register(PositionPacket)
class PositionPacketAdmin(admin.ModelAdmin):
    """Admin interface for managing node position data packets."""

    list_display = (
        "id",
        "packet_id",
        "from_str",
        "to_str",
        "channel",
        "rx_time",
        "position_data",
    )


@admin.register(NodeInfoPacket)
class NodeInfoPacketAdmin(admin.ModelAdmin):
    """Admin interface for managing node information packets."""

    list_display = (
        "id",
        "packet_id",
        "from_str",
        "to_str",
        "channel",
        "rx_time",
        "user_data",
    )


@admin.register(TelemetryPacket)
class TelemetryPacketAdmin(admin.ModelAdmin):
    """Admin interface for managing device telemetry packets."""

    list_display = (
        "id",
        "packet_id",
        "from_str",
        "to_str",
        "channel",
        "rx_time",
        "device_metrics_data",
        "time",
    )

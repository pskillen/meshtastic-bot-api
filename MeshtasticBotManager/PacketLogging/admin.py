from django.contrib import admin

from .models import TelemetryPacket, NodeInfoPacket, PositionPacket, MessagePacket, EncryptedPacket, RawPacket


@admin.register(RawPacket)
class RawPacketAdmin(admin.ModelAdmin):
    list_display = ('id', 'packet_id', 'from_str', 'to_str', 'channel', 'rx_time')


@admin.register(EncryptedPacket)
class EncryptedPacketAdmin(admin.ModelAdmin):
    list_display = ('id', 'packet_id', 'from_str', 'to_str', 'channel', 'rx_time')


@admin.register(MessagePacket)
class MessagePacketAdmin(admin.ModelAdmin):
    list_display = ('id', 'packet_id', 'from_str', 'to_str', 'channel', 'rx_time', 'message_text')


@admin.register(PositionPacket)
class PositionPacketAdmin(admin.ModelAdmin):
    list_display = ('id', 'packet_id', 'from_str', 'to_str', 'channel', 'rx_time', 'position_data')


@admin.register(NodeInfoPacket)
class NodeInfoPacketAdmin(admin.ModelAdmin):
    list_display = ('id', 'packet_id', 'from_str', 'to_str', 'channel', 'rx_time', 'user_data')


@admin.register(TelemetryPacket)
class TelemetryPacketAdmin(admin.ModelAdmin):
    list_display = ('id', 'packet_id', 'from_str', 'to_str', 'channel', 'rx_time', 'device_metrics_data', 'time')

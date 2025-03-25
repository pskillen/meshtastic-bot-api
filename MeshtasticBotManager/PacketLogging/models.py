import uuid
from typing_extensions import deprecated

from django.db import models


class RawPacket(models.Model):
    id = models.UUIDField(primary_key=True, null=False, default=uuid.uuid4, editable=False)
    packet_id = models.BigIntegerField(null=False)
    from_int = models.BigIntegerField(null=False)
    from_str = models.CharField(max_length=9, null=True)
    to_int = models.BigIntegerField(null=True)
    to_str = models.CharField(max_length=9, null=True)
    channel = models.SmallIntegerField(null=True)

    decoded_data = models.JSONField(null=True)
    portnum = models.CharField(max_length=50, null=True)

    hop_limit = models.SmallIntegerField(null=True)
    hop_start = models.SmallIntegerField(null=True)

    rx_time = models.DateTimeField(null=False)
    rx_rssi = models.FloatField(null=True)
    rx_snr = models.FloatField(null=True)

    relay_node = models.BigIntegerField(null=True)


class EncryptedPacket(RawPacket):
    encrypted_data = models.TextField(null=False)


class MessagePacket(RawPacket):
    message_text = models.TextField(null=False)


class MessageReplyPacket(MessagePacket):
    reply_packet_id = models.BigIntegerField(null=False)
    original_message = models.ForeignKey(MessagePacket, null=True, on_delete=models.CASCADE, related_name="reply_to")
    emoji = models.CharField(max_length=2, null=True)


class PositionPacket(RawPacket):
    position_data = models.JSONField(null=False)


class NodeInfoPacket(RawPacket):
    user_data = models.JSONField(null=False)


@deprecated("Use DeviceMetricsPacket or LocalStatsPacket instead")
class TelemetryPacket(RawPacket):
    device_metrics_data = models.JSONField(null=False)
    time = models.DateTimeField(null=False)


class BaseTelemetryPacket(RawPacket):
    time = models.DateTimeField(null=False)


class DeviceMetricsPacket(BaseTelemetryPacket):
    batteryLevel = models.FloatField(null=False)
    voltage = models.FloatField(null=False)
    channelUtilization = models.FloatField(null=False)
    airUtilTx = models.FloatField(null=False)
    uptimeSeconds = models.BigIntegerField(null=False)


class LocalStatsPacket(BaseTelemetryPacket):
    uptimeSeconds = models.BigIntegerField(null=False)
    channelUtilization = models.FloatField(null=False)
    airUtilTx = models.FloatField(null=False)
    numPacketsTx = models.BigIntegerField(null=False)
    numPacketsRx = models.BigIntegerField(null=False)
    numPacketsRxBad = models.BigIntegerField(null=False)
    numOnlineNodes = models.IntegerField(null=False)
    numTotalNodes = models.IntegerField(null=False)
    numRxDupe = models.BigIntegerField(null=False)

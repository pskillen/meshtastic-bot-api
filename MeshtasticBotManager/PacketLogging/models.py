import uuid

from django.db import models
from typing_extensions import deprecated


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
    encrypted_data = models.TextField(null=False, blank=True)


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
    batteryLevel = models.FloatField(null=True)
    voltage = models.FloatField(null=True)
    channelUtilization = models.FloatField(null=True)
    airUtilTx = models.FloatField(null=True)
    uptimeSeconds = models.BigIntegerField(null=True)


class LocalStatsPacket(BaseTelemetryPacket):
    uptimeSeconds = models.BigIntegerField(null=True)
    channelUtilization = models.FloatField(null=True)
    airUtilTx = models.FloatField(null=True)
    numPacketsTx = models.BigIntegerField(null=True)
    numPacketsRx = models.BigIntegerField(null=True)
    numPacketsRxBad = models.BigIntegerField(null=True)
    numOnlineNodes = models.IntegerField(null=True)
    numTotalNodes = models.IntegerField(null=True)
    numRxDupe = models.BigIntegerField(null=True)


class EnvironmentMetricsPacket(BaseTelemetryPacket):
    temperature = models.FloatField(null=True)
    relativeHumidity = models.FloatField(null=True)
    barometricPressure = models.FloatField(null=True)
    gasResistance = models.FloatField(null=True)
    iaq = models.FloatField(null=True)

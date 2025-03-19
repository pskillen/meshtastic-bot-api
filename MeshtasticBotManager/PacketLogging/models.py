import uuid

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


class PositionPacket(RawPacket):
    position_data = models.JSONField(null=False)


class NodeInfoPacket(RawPacket):
    user_data = models.JSONField(null=False)


class TelemetryPacket(RawPacket):
    device_metrics_data = models.JSONField(null=False)
    time = models.DateTimeField(null=False)

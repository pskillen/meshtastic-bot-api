import base64
import datetime

from common.mesh_node_helpers import meshtastic_id_to_hex
from PacketLogging.models import (
    DeviceMetricsPacket,
    EncryptedPacket,
    EnvironmentMetricsPacket,
    LocalStatsPacket,
    MessagePacket,
    MessageReplyPacket,
    NodeInfoPacket,
    PositionPacket,
    RawPacket,
    TelemetryPacket,
)
from rest_framework import serializers
from typing_extensions import deprecated


class RawPacketSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawPacket
        fields = "__all__"


class EncryptedPacketSerializer(RawPacketSerializer):
    class Meta(RawPacketSerializer.Meta):
        model = EncryptedPacket


class MessagePacketSerializer(RawPacketSerializer):
    class Meta(RawPacketSerializer.Meta):
        model = MessagePacket


class PositionPacketSerializer(RawPacketSerializer):
    class Meta(RawPacketSerializer.Meta):
        model = PositionPacket


class NodeInfoPacketSerializer(RawPacketSerializer):
    class Meta(RawPacketSerializer.Meta):
        model = NodeInfoPacket


@deprecated("Use DeviceMetricsPacket or LocalStatsPacket instead")
class TelemetryPacketSerializer(RawPacketSerializer):
    class Meta(RawPacketSerializer.Meta):
        model = TelemetryPacket


class IncomingRawPacketSerializer(serializers.Serializer):
    """
    Used to validate incoming packets before saving them to the database.
    """

    packet_id = serializers.IntegerField()
    from_int = serializers.IntegerField()
    from_str = serializers.CharField(required=False)
    to_int = serializers.IntegerField(required=False)
    to_str = serializers.CharField(required=False)
    channel = serializers.IntegerField(required=False)

    decoded_data = serializers.JSONField(required=False)
    portnum = serializers.CharField(max_length=50, required=False)

    hop_limit = serializers.IntegerField(required=False)
    hop_start = serializers.IntegerField(required=False)

    rx_time = serializers.DateTimeField()
    rx_rssi = serializers.FloatField(required=False)
    rx_snr = serializers.FloatField(required=False)

    relay_node = serializers.IntegerField(required=False)

    def to_internal_value(self, data):
        # Manually remap all our fields, because WHY DJANGO REST FRAMEWORK, WHY!?

        data = data.copy()  # Avoid modifying the original data
        if "id" in data:
            data["packet_id"] = data.pop("id")
        if "from" in data:
            data["from_int"] = data.pop("from")
        if "fromId" in data and data.get("fromId") is not None:
            data["from_str"] = data.pop("fromId")
        else:
            data["from_str"] = meshtastic_id_to_hex(data["from_int"])
        if "to" in data:
            data["to_int"] = data.pop("to")
        if "toId" in data and data.get("toId") is not None:
            data["to_str"] = data.pop("toId")
        else:
            data["to_str"] = meshtastic_id_to_hex(data["to_int"])

        if "hopStart" in data:
            data["hop_start"] = data.pop("hopStart")
        if "hopLimit" in data:
            data["hop_limit"] = data.pop("hopLimit")

        if "rxTime" in data:
            rx_time = data.pop("rxTime")
            if isinstance(rx_time, int):
                data["rx_time"] = datetime.datetime.fromtimestamp(rx_time, tz=datetime.timezone.utc)
            else:
                data["rx_time"] = rx_time
        if "rxRssi" in data:
            data["rx_rssi"] = data.pop("rxRssi")
        if "rxSnr" in data:
            data["rx_snr"] = data.pop("rxSnr")

        if "relayNode" in data:
            data["relay_node"] = data.pop("relayNode")

        decoded_data = data.pop("decoded", None)
        if decoded_data:
            data["decoded_data"] = decoded_data

            if "portnum" in decoded_data:
                data["portnum"] = decoded_data.pop("portnum")

        return super().to_internal_value(data)

    def validate(self, data):
        return super().validate(data)

    def create(self, validated_data):
        return RawPacket.objects.create(**validated_data)


class IncomingEncryptedPacketSerializer(IncomingRawPacketSerializer):
    encrypted_data = serializers.CharField(allow_blank=True)

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        if "encrypted" in data:
            data["encrypted_data"] = data.pop("encrypted")

        return super().to_internal_value(data)

    def create(self, validated_data):
        return EncryptedPacket.objects.create(**validated_data)


class IncomingMessagePacketSerializer(IncomingRawPacketSerializer):
    message_text = serializers.CharField()

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get("decoded", {})
        if "text" in decoded_data:
            data["message_text"] = decoded_data.pop("text")

        return super().to_internal_value(data)

    def create(self, validated_data):
        return MessagePacket.objects.create(**validated_data)


class IncomingMessageReplyPacketSerializer(IncomingMessagePacketSerializer):
    reply_packet_id = serializers.IntegerField()
    emoji = serializers.CharField(max_length=2, required=False)

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get("decoded", {})
        if "replyId" in decoded_data:
            data["reply_packet_id"] = decoded_data.pop("replyId")
        if "emoji" in decoded_data and "payload" in decoded_data and decoded_data["emoji"] == 1:
            # base64 decode the payload field
            data["emoji"] = decoded_data.pop("payload")
            data["emoji"] = base64.b64decode(data["emoji"]).decode("utf-8")

        return super().to_internal_value(data)

    def create(self, validated_data):
        # populate the original_message field
        original_message_id = validated_data.get("reply_packet_id")
        original_message = MessagePacket.objects.filter(packet_id=original_message_id).first()
        if original_message:
            validated_data["original_message"] = original_message
        else:
            validated_data["original_message"] = None

        return MessageReplyPacket.objects.create(**validated_data)


class IncomingPositionPacketSerializer(IncomingRawPacketSerializer):
    position_data = serializers.JSONField()

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get("decoded", {})
        if "position" in decoded_data:
            data["position_data"] = decoded_data.pop("position")

        return super().to_internal_value(data)

    def create(self, validated_data):
        return PositionPacket.objects.create(**validated_data)


class IncomingNodeInfoPacketSerializer(IncomingRawPacketSerializer):
    user_data = serializers.JSONField()

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get("decoded", {})
        if "user" in decoded_data:
            data["user_data"] = decoded_data.pop("user")

        return super().to_internal_value(data)

    def create(self, validated_data):
        return NodeInfoPacket.objects.create(**validated_data)


class IncomingDeviceMetricsPacketSerializer(IncomingRawPacketSerializer):
    batteryLevel = serializers.FloatField(required=False, allow_null=True)
    voltage = serializers.FloatField(required=False, allow_null=True)
    channelUtilization = serializers.FloatField(required=False, allow_null=True)
    airUtilTx = serializers.FloatField(required=False, allow_null=True)
    uptimeSeconds = serializers.IntegerField(required=False, allow_null=True)
    time = serializers.DateTimeField(required=True)

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get("decoded", {})
        if "telemetry" in decoded_data:
            telemetry_data = decoded_data.pop("telemetry", {})
            telemetry_time = telemetry_data.pop("time", None)
            if isinstance(telemetry_time, int):
                data["time"] = datetime.datetime.fromtimestamp(telemetry_time, tz=datetime.timezone.utc)
            else:
                data["time"] = telemetry_time

            device_metrics = telemetry_data.pop("deviceMetrics", {})
            data["batteryLevel"] = device_metrics.pop("batteryLevel", None)
            data["voltage"] = device_metrics.pop("voltage", None)
            data["channelUtilization"] = device_metrics.pop("channelUtilization", None)
            data["airUtilTx"] = device_metrics.pop("airUtilTx", None)
            data["uptimeSeconds"] = device_metrics.pop("uptimeSeconds", None)

        return super().to_internal_value(data)

    def create(self, validated_data):
        return DeviceMetricsPacket.objects.create(**validated_data)


class IncomingLocalStatsPacketSerializer(IncomingRawPacketSerializer):
    uptimeSeconds = serializers.IntegerField(required=False, allow_null=True)
    channelUtilization = serializers.FloatField(required=False, allow_null=True)
    airUtilTx = serializers.FloatField(required=False, allow_null=True)
    numPacketsTx = serializers.IntegerField(required=False, allow_null=True)
    numPacketsRx = serializers.IntegerField(required=False, allow_null=True)
    numPacketsRxBad = serializers.IntegerField(required=False, allow_null=True)
    numOnlineNodes = serializers.IntegerField(required=False, allow_null=True)
    numTotalNodes = serializers.IntegerField(required=False, allow_null=True)
    numRxDupe = serializers.IntegerField(required=False, allow_null=True)
    time = serializers.DateTimeField(required=True)

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get("decoded", {})
        if "telemetry" in decoded_data:
            telemetry_data = decoded_data.pop("telemetry", {})
            telemetry_time = telemetry_data.pop("time", None)
            if isinstance(telemetry_time, int):
                data["time"] = datetime.datetime.fromtimestamp(telemetry_time, tz=datetime.timezone.utc)
            else:
                data["time"] = telemetry_time

            local_stats = telemetry_data.pop("localStats", {})
            data["uptimeSeconds"] = local_stats.pop("uptimeSeconds", None)
            data["channelUtilization"] = local_stats.pop("channelUtilization", None)
            data["airUtilTx"] = local_stats.pop("airUtilTx", None)
            data["numPacketsTx"] = local_stats.pop("numPacketsTx", None)
            data["numPacketsRx"] = local_stats.pop("numPacketsRx", None)
            data["numPacketsRxBad"] = local_stats.pop("numPacketsRxBad", None)
            data["numOnlineNodes"] = local_stats.pop("numOnlineNodes", None)
            data["numTotalNodes"] = local_stats.pop("numTotalNodes", None)
            data["numRxDupe"] = local_stats.pop("numRxDupe", None)

        return super().to_internal_value(data)

    def create(self, validated_data):
        return LocalStatsPacket.objects.create(**validated_data)


class IncomingEnvironmentMetricsPacketSerializer(IncomingRawPacketSerializer):
    temperature = serializers.FloatField(required=False, allow_null=True)
    relativeHumidity = serializers.FloatField(required=False, allow_null=True)
    barometricPressure = serializers.FloatField(required=False, allow_null=True)
    gasResistance = serializers.FloatField(required=False, allow_null=True)
    iaq = serializers.FloatField(required=False, allow_null=True)
    time = serializers.DateTimeField(required=True)

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get("decoded", {})
        if "telemetry" in decoded_data:
            telemetry_data = decoded_data.pop("telemetry", {})
            telemetry_time = telemetry_data.pop("time", None)
            if isinstance(telemetry_time, int):
                data["time"] = datetime.datetime.fromtimestamp(telemetry_time, tz=datetime.timezone.utc)
            else:
                data["time"] = telemetry_time

            environment_metrics = telemetry_data.pop("environmentMetrics", {})
            data["temperature"] = environment_metrics.pop("temperature", None)
            data["relativeHumidity"] = environment_metrics.pop("relativeHumidity", None)
            data["barometricPressure"] = environment_metrics.pop("barometricPressure", None)
            data["gasResistance"] = environment_metrics.pop("gasResistance", None)
            data["iaq"] = environment_metrics.pop("iaq", None)

        return super().to_internal_value(data)

    def create(self, validated_data):
        return EnvironmentMetricsPacket.objects.create(**validated_data)

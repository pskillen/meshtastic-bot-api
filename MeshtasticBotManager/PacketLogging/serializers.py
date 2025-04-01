"""Serializers for converting mesh network packets to and from JSON."""

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
    """Serializer for raw mesh network packets."""

    class Meta:
        """Meta class for RawPacketSerializer."""

        model = RawPacket
        fields = "__all__"


class EncryptedPacketSerializer(RawPacketSerializer):
    """Serializer for encrypted mesh network packets."""

    class Meta(RawPacketSerializer.Meta):
        """Meta class for EncryptedPacketSerializer."""

        model = EncryptedPacket


class MessagePacketSerializer(RawPacketSerializer):
    """Serializer for text message packets."""

    class Meta(RawPacketSerializer.Meta):
        """Meta class for MessagePacketSerializer."""

        model = MessagePacket


class PositionPacketSerializer(RawPacketSerializer):
    """Serializer for node position data packets."""

    class Meta(RawPacketSerializer.Meta):
        """Meta class for PositionPacketSerializer."""

        model = PositionPacket


class NodeInfoPacketSerializer(RawPacketSerializer):
    """Serializer for node information packets."""

    class Meta(RawPacketSerializer.Meta):
        """Meta class for NodeInfoPacketSerializer."""

        model = NodeInfoPacket


@deprecated("Use DeviceMetricsPacket or LocalStatsPacket instead")
class TelemetryPacketSerializer(RawPacketSerializer):
    """Serializer for device telemetry packets (deprecated)."""

    class Meta(RawPacketSerializer.Meta):
        """Meta class for TelemetryPacketSerializer."""

        model = TelemetryPacket


class IncomingRawPacketSerializer(serializers.Serializer):
    """Serializer for validating incoming raw packets before database storage."""

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
        """Convert the incoming data to internal values.

        Args:
            data: The incoming data to convert.

        Returns:
            dict: The converted data.
        """
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
        """Validate the incoming data.

        Args:
            data: The data to validate.

        Returns:
            dict: The validated data.
        """
        return super().validate(data)

    def create(self, validated_data):
        """Create a new RawPacket instance.

        Args:
            validated_data: The validated data to create the packet with.

        Returns:
            RawPacket: The created packet instance.
        """
        return RawPacket.objects.create(**validated_data)


class IncomingEncryptedPacketSerializer(IncomingRawPacketSerializer):
    """Serializer for validating incoming encrypted packets."""

    encrypted_data = serializers.CharField(allow_blank=True)

    def to_internal_value(self, data):
        """Convert the incoming data to internal values.

        Args:
            data: The incoming data to convert.

        Returns:
            dict: The converted data.
        """
        data = data.copy()  # Avoid modifying the original data

        if "encrypted" in data:
            data["encrypted_data"] = data.pop("encrypted")

        return super().to_internal_value(data)

    def create(self, validated_data):
        """Create a new EncryptedPacket instance.

        Args:
            validated_data: The validated data to create the packet with.

        Returns:
            EncryptedPacket: The created packet instance.
        """
        return EncryptedPacket.objects.create(**validated_data)


class IncomingMessagePacketSerializer(IncomingRawPacketSerializer):
    """Serializer for validating incoming text message packets."""

    message_text = serializers.CharField()

    def to_internal_value(self, data):
        """Convert the incoming data to internal values.

        Args:
            data: The incoming data to convert.

        Returns:
            dict: The converted data.
        """
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get("decoded", {})
        if "text" in decoded_data:
            data["message_text"] = decoded_data.pop("text")

        return super().to_internal_value(data)

    def create(self, validated_data):
        """Create a new MessagePacket instance.

        Args:
            validated_data: The validated data to create the packet with.

        Returns:
            MessagePacket: The created packet instance.
        """
        return MessagePacket.objects.create(**validated_data)


class IncomingMessageReplyPacketSerializer(IncomingMessagePacketSerializer):
    """Serializer for validating incoming message reply packets."""

    reply_packet_id = serializers.IntegerField()
    emoji = serializers.CharField(max_length=2, required=False)

    def to_internal_value(self, data):
        """Convert the incoming data to internal values.

        Args:
            data: The incoming data to convert.

        Returns:
            dict: The converted data.
        """
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
        """Create a new MessageReplyPacket instance.

        Args:
            validated_data: The validated data to create the packet with.

        Returns:
            MessageReplyPacket: The created packet instance.
        """
        # populate the original_message field
        original_message_id = validated_data.get("reply_packet_id")
        original_message = MessagePacket.objects.filter(packet_id=original_message_id).first()
        if original_message:
            validated_data["original_message"] = original_message
        else:
            validated_data["original_message"] = None

        return MessageReplyPacket.objects.create(**validated_data)


class IncomingPositionPacketSerializer(IncomingRawPacketSerializer):
    """Serializer for validating incoming position data packets."""

    position_data = serializers.JSONField()

    def to_internal_value(self, data):
        """Convert the incoming data to internal values.

        Args:
            data: The incoming data to convert.

        Returns:
            dict: The converted data.
        """
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get("decoded", {})
        if "position" in decoded_data:
            data["position_data"] = decoded_data.pop("position")

        return super().to_internal_value(data)

    def create(self, validated_data):
        """Create a new PositionPacket instance.

        Args:
            validated_data: The validated data to create the packet with.

        Returns:
            PositionPacket: The created packet instance.
        """
        return PositionPacket.objects.create(**validated_data)


class IncomingNodeInfoPacketSerializer(IncomingRawPacketSerializer):
    """Serializer for validating incoming node information packets."""

    user_data = serializers.JSONField()

    def to_internal_value(self, data):
        """Convert the incoming data to internal values.

        Args:
            data: The incoming data to convert.

        Returns:
            dict: The converted data.
        """
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get("decoded", {})
        if "user" in decoded_data:
            data["user_data"] = decoded_data.pop("user")

        return super().to_internal_value(data)

    def create(self, validated_data):
        """Create a new NodeInfoPacket instance.

        Args:
            validated_data: The validated data to create the packet with.

        Returns:
            NodeInfoPacket: The created packet instance.
        """
        return NodeInfoPacket.objects.create(**validated_data)


class IncomingDeviceMetricsPacketSerializer(IncomingRawPacketSerializer):
    """Serializer for validating incoming device metrics packets."""

    batteryLevel = serializers.FloatField(required=False, allow_null=True)
    voltage = serializers.FloatField(required=False, allow_null=True)
    channelUtilization = serializers.FloatField(required=False, allow_null=True)
    airUtilTx = serializers.FloatField(required=False, allow_null=True)
    uptimeSeconds = serializers.IntegerField(required=False, allow_null=True)
    time = serializers.DateTimeField(required=True)

    def to_internal_value(self, data):
        """Convert the incoming data to internal values.

        Args:
            data: The incoming data to convert.

        Returns:
            dict: The converted data.
        """
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
        """Create a new DeviceMetricsPacket instance.

        Args:
            validated_data: The validated data to create the packet with.

        Returns:
            DeviceMetricsPacket: The created packet instance.
        """
        return DeviceMetricsPacket.objects.create(**validated_data)


class IncomingLocalStatsPacketSerializer(IncomingRawPacketSerializer):
    """Serializer for validating incoming local statistics packets."""

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
        """Convert the incoming data to internal values.

        Args:
            data: The incoming data to convert.

        Returns:
            dict: The converted data.
        """
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
        """Create a new LocalStatsPacket instance.

        Args:
            validated_data: The validated data to create the packet with.

        Returns:
            LocalStatsPacket: The created packet instance.
        """
        return LocalStatsPacket.objects.create(**validated_data)


class IncomingEnvironmentMetricsPacketSerializer(IncomingRawPacketSerializer):
    """Serializer for validating incoming environment metrics packets."""

    temperature = serializers.FloatField(required=False, allow_null=True)
    relativeHumidity = serializers.FloatField(required=False, allow_null=True)
    barometricPressure = serializers.FloatField(required=False, allow_null=True)
    gasResistance = serializers.FloatField(required=False, allow_null=True)
    iaq = serializers.FloatField(required=False, allow_null=True)
    time = serializers.DateTimeField(required=True)

    def to_internal_value(self, data):
        """Convert the incoming data to internal values.

        Args:
            data: The incoming data to convert.

        Returns:
            dict: The converted data.
        """
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
        """Create a new EnvironmentMetricsPacket instance.

        Args:
            validated_data: The validated data to create the packet with.

        Returns:
            EnvironmentMetricsPacket: The created packet instance.
        """
        return EnvironmentMetricsPacket.objects.create(**validated_data)

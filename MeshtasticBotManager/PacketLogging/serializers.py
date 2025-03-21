import base64
import datetime

from rest_framework import serializers

from PacketLogging.models import TelemetryPacket, NodeInfoPacket, PositionPacket, MessagePacket, RawPacket, \
    EncryptedPacket, MessageReplyPacket


class RawPacketSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawPacket
        fields = '__all__'


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
        if "fromId" in data:
            data["from_str"] = data.pop("fromId")
        if "to" in data:
            data["to_int"] = data.pop("to")
        if "toId" in data:
            data["to_str"] = data.pop("toId")

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

            if 'portnum' in decoded_data:
                data['portnum'] = decoded_data.pop('portnum')

        return super().to_internal_value(data)

    def validate(self, data):
        return super().validate(data)

    def create(self, validated_data):
        return RawPacket.objects.create(**validated_data)


class IncomingEncryptedPacketSerializer(IncomingRawPacketSerializer):
    encrypted_data = serializers.CharField()

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        if 'encrypted' in data:
            data['encrypted_data'] = data.pop('encrypted')

        return super().to_internal_value(data)

    def create(self, validated_data):
        return EncryptedPacket.objects.create(**validated_data)


class IncomingMessagePacketSerializer(IncomingRawPacketSerializer):
    message_text = serializers.CharField()

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get('decoded', {})
        if 'text' in decoded_data:
            data['message_text'] = decoded_data.pop('text')

        return super().to_internal_value(data)

    def create(self, validated_data):
        return MessagePacket.objects.create(**validated_data)


class IncomingMessageReplyPacketSerializer(IncomingMessagePacketSerializer):
    reply_packet_id = serializers.IntegerField()
    emoji = serializers.CharField(max_length=2, required=False)

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get('decoded', {})
        if 'replyId' in decoded_data:
            data['reply_packet_id'] = decoded_data.pop('replyId')
        if 'emoji' in decoded_data and 'payload' in decoded_data and decoded_data['emoji'] == 1:
            # base64 decode the payload field
            data['emoji'] = decoded_data.pop('payload')
            data['emoji'] = base64.b64decode(data['emoji']).decode('utf-8')

        return super().to_internal_value(data)

    def create(self, validated_data):
        # populate the original_message field
        original_message_id = validated_data.get('reply_packet_id')
        original_message = MessagePacket.objects.get(packet_id=original_message_id)
        validated_data['original_message'] = original_message

        return MessageReplyPacket.objects.create(**validated_data)


class IncomingPositionPacketSerializer(IncomingRawPacketSerializer):
    position_data = serializers.JSONField()

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get('decoded', {})
        if 'position' in decoded_data:
            data['position_data'] = decoded_data.pop('position')

        return super().to_internal_value(data)

    def create(self, validated_data):
        return PositionPacket.objects.create(**validated_data)


class IncomingNodeInfoPacketSerializer(IncomingRawPacketSerializer):
    user_data = serializers.JSONField()

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get('decoded', {})
        if 'user' in decoded_data:
            data['user_data'] = decoded_data.pop('user')

        return super().to_internal_value(data)

    def create(self, validated_data):
        return NodeInfoPacket.objects.create(**validated_data)


class IncomingTelemetryPacketSerializer(IncomingRawPacketSerializer):
    device_metrics_data = serializers.JSONField()
    time = serializers.DateTimeField()

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        decoded_data = data.get('decoded', {})
        if 'telemetry' in decoded_data:
            telemetry_data = decoded_data.pop('telemetry', {})
            data['device_metrics_data'] = telemetry_data.pop('deviceMetrics', None)
            telemetry_time = telemetry_data.pop('time', None)
            if isinstance(telemetry_time, int):
                data["time"] = datetime.datetime.fromtimestamp(telemetry_time, tz=datetime.timezone.utc)
            else:
                data["time"] = telemetry_time

        return super().to_internal_value(data)

    def create(self, validated_data):
        return TelemetryPacket.objects.create(**validated_data)

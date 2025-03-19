from rest_framework import serializers

from NodeDB.models import MeshNode, MeshUser, Position, DeviceMetrics
from common.mesh_node_helpers import meshtastic_id_to_hex, meshtastic_hex_to_int



class MeshUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeshUser
        exclude = ['node', 'id']


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        exclude = ['node', 'id']


class DeviceMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceMetrics
        exclude = ['node', 'id']


class MeshNodeSerializer(serializers.HyperlinkedModelSerializer):
    user = MeshUserSerializer(required=False)
    position = PositionSerializer(many=False, required=False)
    device_metrics = DeviceMetricsSerializer(many=False, required=False)

    class Meta:
        model = MeshNode
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['id'] = meshtastic_id_to_hex(instance.id)

        if hasattr(instance, 'user') and instance.user:
            representation['user'] = MeshUserSerializer(instance.user).data
        if hasattr(instance, 'position_list') and instance.position_list.exists():
            representation['position'] = PositionSerializer(instance.position_list.last()).data
        if hasattr(instance, 'device_metrics_list') and instance.device_metrics_list.exists():
            representation['device_metrics'] = DeviceMetricsSerializer(instance.device_metrics_list.last()).data

        return representation

    def to_internal_value(self, data):
        data = data.copy()  # Avoid modifying the original data

        if 'id' in data and isinstance(data['id'], str):
            data['id'] = meshtastic_hex_to_int(data['id'])
            self.initial_data['id'] = data['id']

        if 'id_str' not in data:
            data['id_str'] = meshtastic_id_to_hex(data['id'])
            self.initial_data['id_str'] = data['id_str']

        return super().to_internal_value(data)

    def create(self, validated_data):
        mesh_user_data = validated_data.pop('user', None)
        position_data = validated_data.pop('position', None)
        device_metrics_data = validated_data.pop('device_metrics', None)

        # Ensure we store the ID in int format
        if 'id' not in validated_data:
            validated_data['id'] = self.initial_data['id']
        if isinstance(validated_data['id'], str):
            validated_data['id'] = meshtastic_hex_to_int(self.validated_data['id'])

        validated_data['id_str'] = meshtastic_id_to_hex(validated_data['id'])

        mesh_node: MeshNode = super().create(validated_data)

        if mesh_user_data:
            MeshUser.objects.create(node=mesh_node, **mesh_user_data)

        if position_data:
            Position.objects.create(node=mesh_node, **position_data)

        if device_metrics_data:
            DeviceMetrics.objects.create(node=mesh_node, **device_metrics_data)

        return mesh_node

    def update(self, instance, validated_data):
        validated_data['id_str'] = meshtastic_id_to_hex(instance.id)

        user_data = validated_data.pop('user', None)
        position_data = validated_data.pop('position', None)
        device_metrics_data = validated_data.pop('device_metrics', None)

        instance = super().update(instance, validated_data)

        # There's only ever 1 MeshUser per MeshNode
        if user_data:
            MeshUser.objects.update_or_create(node=instance, defaults=user_data)

        # This may be a new position, or the bot may have restarted, but log it anyway
        if position_data:
            Position.objects.create(node=instance, **position_data)

        # This may be new metrics, or the bot may have restarted, but log it anyway
        if device_metrics_data:
            DeviceMetrics.objects.create(node=instance, **device_metrics_data)

        return instance

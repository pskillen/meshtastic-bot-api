from rest_framework import viewsets
from rest_framework.response import Response

from common.mesh_node_helpers import meshtastic_hex_to_int
from .models import MeshNode
from .serializers import MeshNodeSerializer


class MeshNodeViewSet(viewsets.ModelViewSet):
    queryset = MeshNode.objects.all()
    serializer_class = MeshNodeSerializer

    def create(self, request, *args, **kwargs):
        # Extract the unique identifier from the request data
        node_id = request.data.get('id')

        # ensure we're working with an int nodeid
        if isinstance(node_id, str):
            node_id = meshtastic_hex_to_int(node_id)
            request.data['id'] = node_id

        if node_id:
            # Try to find an existing object with the same id
            try:
                instance = MeshNode.objects.get(id=node_id)
                serializer = self.get_serializer(instance, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data)
            except MeshNode.DoesNotExist:
                pass

        # If the object does not exist, create a new one
        return super().create(request, *args, **kwargs)

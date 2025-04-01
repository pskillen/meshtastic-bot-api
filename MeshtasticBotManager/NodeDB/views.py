"""Views for managing mesh network nodes through the REST API."""

from common.mesh_node_helpers import meshtastic_hex_to_int
from rest_framework import viewsets
from rest_framework.response import Response

from .models import MeshNode
from .serializers import MeshNodeSerializer


class MeshNodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing mesh nodes, supporting create, read, update, and delete operations."""

    queryset = MeshNode.objects.all()
    serializer_class = MeshNodeSerializer

    def create(self, request, *args, **kwargs):
        """Create or update a mesh node based on its ID.

        If a node with the given ID already exists, update it instead of creating a new one.
        This handles both hex and integer node IDs.
        """
        # Extract the unique identifier from the request data
        node_id = request.data.get("id")

        # ensure we're working with an int nodeid
        if isinstance(node_id, str):
            node_id = meshtastic_hex_to_int(node_id)
            request.data["id"] = node_id

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

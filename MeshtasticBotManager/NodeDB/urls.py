from rest_framework import routers

from NodeDB.views import MeshNodeViewSet

api_router = routers.DefaultRouter()
api_router.register(r'nodes', MeshNodeViewSet)

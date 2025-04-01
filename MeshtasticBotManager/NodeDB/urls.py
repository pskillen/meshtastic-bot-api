from NodeDB.views import MeshNodeViewSet
from rest_framework import routers

api_router = routers.DefaultRouter()
api_router.register(r'', MeshNodeViewSet)

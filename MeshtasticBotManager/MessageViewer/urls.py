"""URL configuration for the MessageViewer app."""

from django.urls import path

from MessageViewer.views.channels.channel_view import MessageHistoryView
from MessageViewer.views.nodes.node_api import NodeViewSet
from MessageViewer.views.nodes.node_details import NodeDetailView
from MessageViewer.views.nodes.node_list_view import NodeListView
from MessageViewer.views.stats.stats_api import StatsViewSet
from rest_framework import routers

api_router = routers.DefaultRouter()
api_router.register("nodes", NodeViewSet, basename="node_detail")
api_router.register("stats", StatsViewSet, basename="stats")

urlpatterns = [
    path("nodes/", NodeListView.as_view(), name="nodes"),
    path("node/<int:pk>/", NodeDetailView.as_view(), name="node_detail"),
    path("messages/", MessageHistoryView.as_view(), name="channel"),
]

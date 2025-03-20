from django.urls import path

from MessageViewer.views.channels.channel_view import MessageHistoryView
from MessageViewer.views.nodes.node_details import NodeDetailView
from MessageViewer.views.nodes.node_list_view import NodeListView

urlpatterns = [
    path('nodes/', NodeListView.as_view(), name='nodes'),
    path('node/<int:pk>/', NodeDetailView.as_view(), name='node_detail'),
    path('messages/', MessageHistoryView.as_view(), name='channel'),
]

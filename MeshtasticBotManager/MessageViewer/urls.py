from django.urls import path

from MessageViewer.views.channels.channel_view import MessageHistoryView

urlpatterns = [
    path('messages/', MessageHistoryView.as_view(), name='channel'),
]

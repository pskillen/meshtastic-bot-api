from django.urls import path
from .views import message_history

urlpatterns = [
    path('channel/', message_history, name='channel'),
]

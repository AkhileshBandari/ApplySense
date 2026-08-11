from django.urls import path
from .views import (
    ChatThreadListCreateView,
    ChatThreadDetailView,
    ChatMessageListCreateView
)

urlpatterns = [
    path('threads/', ChatThreadListCreateView.as_view(), name='thread-list-create'),
    path('threads/<int:pk>/', ChatThreadDetailView.as_view(), name='thread-detail'),
    path('threads/<int:thread_id>/messages/', ChatMessageListCreateView.as_view(), name='message-list-create'),
]

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import ChatThread, ChatMessage
from .serializers import ChatThreadSerializer, ChatThreadListSerializer, ChatMessageSerializer
from .services.conversation_service import ConversationService

class ChatThreadListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ChatThreadSerializer
        return ChatThreadListSerializer

    def get_queryset(self):
        return ChatThread.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatThreadDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatThreadSerializer

    def get_queryset(self):
        return ChatThread.objects.filter(user=self.request.user)


class ChatMessageListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, thread_id):
        thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
        # In a real app we might paginate here, but for now return all
        messages = thread.messages.all().order_by('created_at')
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, thread_id):
        thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
        content = request.data.get('content')
        
        if not content:
            return Response({'error': 'Message content is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Process the message via the ConversationService
        conv_service = ConversationService()
        assistant_msg = conv_service.process_message(thread, content)
        
        # We can just return the new messages or the assistant message.
        serializer = ChatMessageSerializer(assistant_msg)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

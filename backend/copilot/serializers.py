from rest_framework import serializers
from .models import ChatThread, ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'role',
            'content',
            'intent',
            'evidence',
            'recommendations',
            'warnings',
            'context_used',
            'created_at',
            'error_state'
        ]
        read_only_fields = fields

class ChatThreadSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatThread
        fields = [
            'id',
            'title',
            'status',
            'job_id',
            'application_id',
            'resume_version_id',
            'created_at',
            'updated_at',
            'last_message_at',
            'messages'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'last_message_at',
            'messages'
        ]
        
    def get_messages(self, obj):
        # We optionally return recent messages in the thread listing or detail view.
        # It's better to fetch messages via the message API but a quick snapshot helps.
        # Limiting to last 5 messages to keep payload size small for list view.
        messages = obj.messages.all().order_by('-created_at')[:5]
        # Reverse to chronological order
        return ChatMessageSerializer(reversed(messages), many=True).data

class ChatThreadListSerializer(serializers.ModelSerializer):
    # Lightweight serializer for the sidebar
    class Meta:
        model = ChatThread
        fields = [
            'id',
            'title',
            'status',
            'job_id',
            'application_id',
            'resume_version_id',
            'updated_at'
        ]
        read_only_fields = fields

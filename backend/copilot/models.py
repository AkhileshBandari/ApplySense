from django.db import models
from django.conf import settings

class ChatThread(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_threads')
    title = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=50, default='ACTIVE')
    
    # Context bindings
    job = models.ForeignKey('jobs.Job', on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_threads')
    application = models.ForeignKey('applications.Application', on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_threads')
    resume_version = models.ForeignKey('resumes.ResumeVersion', on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_threads')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]

    def __str__(self):
        return f"Thread {self.id} for {self.user.username}"


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('USER', 'User'),
        ('ASSISTANT', 'Assistant'),
        ('SYSTEM', 'System')
    ]
    
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    content = models.TextField()
    
    intent = models.CharField(max_length=100, blank=True)
    evidence = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    context_used = models.JSONField(default=list, blank=True)
    
    model_provider = models.CharField(max_length=100, blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    prompt_version = models.CharField(max_length=100, blank=True)
    
    token_usage = models.JSONField(default=dict, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    error_state = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at']),
        ]

    def __str__(self):
        return f"{self.role} message in thread {self.thread.id}"

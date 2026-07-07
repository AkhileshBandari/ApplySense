from django.db import models
from django.conf import settings
from jobs.models import Job

class Application(models.Model):
    STATUS_CHOICES = (
        ('Saved', 'Saved'),
        ('Applied', 'Applied'),
        ('Under Review', 'Under Review'),
        ('Assessment', 'Assessment'),
        ('Interview', 'Interview'),
        ('Offer', 'Offer'),
        ('Rejected', 'Rejected'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Saved')
    match_score = models.IntegerField(default=0)
    match_details = models.JSONField(null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'job')

    def __str__(self):
        return f"{self.user.email} -> {self.job.title} ({self.status})"

class Interview(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    stage = models.CharField(max_length=100) # Technical, HR, System Design, etc.
    scheduled_at = models.DateTimeField()
    location_type = models.CharField(max_length=50, default='Virtual') # Virtual, On-Site
    video_url = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Interview for {self.application.job.title} - {self.stage}"

class ApplicationNote(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note on {self.application.job.title} at {self.created_at}"

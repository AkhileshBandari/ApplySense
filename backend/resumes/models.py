from django.db import models
from django.conf import settings

class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to='resumes/')
    file_name = models.CharField(max_length=255)
    parsed_text = models.TextField(blank=True)
    health_score = models.IntegerField(default=0)
    ats_score = models.IntegerField(default=0)
    parsed_data = models.JSONField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_name} uploaded by {self.user.email}"

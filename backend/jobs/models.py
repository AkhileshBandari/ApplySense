from django.db import models

class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=150, blank=True)
    portal_type = models.CharField(max_length=50, default='Custom') # Greenhouse, Lever, Ashby, etc.
    source_url = models.URLField(max_length=500, blank=True, null=True, unique=True)
    description = models.TextField()
    requirements = models.JSONField(null=True, blank=True)
    discovered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

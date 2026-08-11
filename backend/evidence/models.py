from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import os

# Note: In production this would use proper vaulting or secure env vars.
# We'll mock a simple symmetric encryption for token storage.
ENCRYPTION_KEY = os.environ.get('EVIDENCE_ENCRYPTION_KEY', Fernet.generate_key().decode('utf-8'))
if not ENCRYPTION_KEY.encode().isalnum() and len(ENCRYPTION_KEY) != 44:
    # ensure valid fernet key if none provided
    pass # we assume fernet keys are 44 bytes base64 encoded
    
class GitHubConnection(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='github_connection')
    github_user_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    github_username = models.CharField(max_length=255, null=True, blank=True)
    profile_url = models.URLField(blank=True)
    avatar_url = models.URLField(blank=True)
    account_type = models.CharField(max_length=50, blank=True)
    
    connected_at = models.DateTimeField(auto_now_add=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    
    sync_status = models.CharField(max_length=50, default='PENDING')
    sync_error_code = models.CharField(max_length=50, blank=True)
    sync_error_message = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    _encrypted_access_token = models.BinaryField(null=True, blank=True)
    
    def set_token(self, raw_token: str):
        if raw_token:
            f = Fernet(ENCRYPTION_KEY.encode())
            self._encrypted_access_token = f.encrypt(raw_token.encode())
        else:
            self._encrypted_access_token = None
            
    def get_token(self) -> str:
        if self._encrypted_access_token:
            try:
                f = Fernet(ENCRYPTION_KEY.encode())
                return f.decrypt(self._encrypted_access_token).decode()
            except Exception:
                return None
        return None

    def __str__(self):
        return f"{self.user.email} GitHub Connection"


class GitHubSyncRun(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='github_sync_runs')
    connection = models.ForeignKey(GitHubConnection, on_delete=models.CASCADE, related_name='sync_runs')
    
    status = models.CharField(max_length=50, default='PENDING') # PENDING, RUNNING, COMPLETED, PARTIAL, FAILED, RATE_LIMITED
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    repositories_discovered = models.IntegerField(default=0)
    repositories_updated = models.IntegerField(default=0)
    repositories_failed = models.IntegerField(default=0)
    
    rate_limit_remaining = models.IntegerField(null=True, blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"Sync {self.id} for {self.user.email}"


class CandidateRepository(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='github_repositories')
    github_connection = models.ForeignKey(GitHubConnection, on_delete=models.CASCADE, related_name='repositories')
    
    external_repository_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    repository_url = models.URLField()
    homepage_url = models.URLField(blank=True, null=True)
    default_branch = models.CharField(max_length=100, default='main')
    
    visibility = models.CharField(max_length=50, default='public')
    is_fork = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_template = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    
    created_at_external = models.DateTimeField(null=True, blank=True)
    updated_at_external = models.DateTimeField(null=True, blank=True)
    pushed_at_external = models.DateTimeField(null=True, blank=True)
    
    stars = models.IntegerField(default=0)
    forks = models.IntegerField(default=0)
    watchers = models.IntegerField(default=0)
    open_issues = models.IntegerField(default=0)
    
    primary_language = models.CharField(max_length=100, blank=True, null=True)
    repository_topics = models.JSONField(default=list, blank=True)
    
    license = models.CharField(max_length=100, blank=True, null=True)
    size = models.IntegerField(default=0)
    
    last_synced_at = models.DateTimeField(auto_now=True)
    raw_metadata_snapshot = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.full_name


class CandidateSkillEvidence(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='skill_evidence')
    
    # We reference taxonomy to keep things normalized across the system
    skill_taxonomy = models.ForeignKey('learning.SkillTaxonomy', on_delete=models.CASCADE, related_name='evidence')
    
    source_type = models.CharField(max_length=50) # GITHUB, PORTFOLIO
    
    repository = models.ForeignKey(CandidateRepository, on_delete=models.SET_NULL, null=True, blank=True, related_name='evidence_items')
    portfolio_project = models.ForeignKey('PortfolioProject', on_delete=models.SET_NULL, null=True, blank=True, related_name='evidence_items')
    
    evidence_type = models.CharField(max_length=100) # DEPENDENCY_FILE, README, REPOSITORY_TOPIC, PORTFOLIO_CLAIM
    evidence_reference = models.CharField(max_length=255, blank=True) # e.g. path to file or url
    evidence_summary = models.TextField(blank=True)
    
    confidence = models.CharField(max_length=50, default='MEDIUM') # HIGH, MEDIUM, LOW
    status = models.CharField(max_length=50, default='DETECTED') # DETECTED, REVIEW_REQUIRED, ACCEPTED, REJECTED, STALE
    
    first_observed_at = models.DateTimeField(auto_now_add=True)
    last_observed_at = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.skill_taxonomy.canonical_name} via {self.source_type} for {self.user.email}"


class PortfolioConnection(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolio_connection')
    portfolio_url = models.URLField()
    normalized_url = models.URLField()
    
    status = models.CharField(max_length=50, default='PENDING')
    last_analyzed_at = models.DateTimeField(null=True, blank=True)
    analysis_status = models.CharField(max_length=50, default='PENDING')
    error_code = models.CharField(max_length=50, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Portfolio {self.portfolio_url} for {self.user.email}"


class PortfolioProject(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolio_projects')
    portfolio = models.ForeignKey(PortfolioConnection, on_delete=models.CASCADE, related_name='projects')
    
    external_key = models.CharField(max_length=255) # Hash of url or title to avoid dupes
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    project_url = models.URLField(blank=True, null=True)
    repository_url = models.URLField(blank=True, null=True)
    live_demo_url = models.URLField(blank=True, null=True)
    
    technologies_detected = models.JSONField(default=list, blank=True)
    evidence_snapshot = models.JSONField(default=dict, blank=True)
    
    first_observed_at = models.DateTimeField(auto_now_add=True)
    last_observed_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, default='ACTIVE')
    
    def __str__(self):
        return self.title

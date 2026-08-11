import requests
from django.utils import timezone
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from evidence.models import (
    GitHubConnection, GitHubSyncRun, CandidateRepository, CandidateSkillEvidence
)
from learning.models import SkillTaxonomy
from learning.services.taxonomy import SkillRequirementNormalizationService

class GitHubRepositoryAnalysisService:
    """
    Handles synchronization of a user's GitHub repositories and extracts technical evidence
    deterministically without hallucinating skills.
    """
    BASE_URL = "https://api.github.com"
    
    @classmethod
    def get_headers(cls, token: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if token:
            headers["Authorization"] = f"token {token}"
        return headers
        
    @classmethod
    def sync_user_repositories(cls, connection: GitHubConnection) -> GitHubSyncRun:
        sync_run = GitHubSyncRun.objects.create(
            user=connection.user,
            connection=connection,
            status='RUNNING'
        )
        
        token = connection.get_token()
        username = connection.github_username
        
        if not username:
            sync_run.status = 'FAILED'
            sync_run.error_code = 'MISSING_USERNAME'
            sync_run.error_message = 'GitHub username is required for sync.'
            sync_run.completed_at = timezone.now()
            sync_run.save()
            return sync_run
            
        try:
            # We'll fetch the public repositories for the user
            # In a real app we'd paginate. We'll do 1 page of 100 for this implementation.
            url = f"{cls.BASE_URL}/users/{username}/repos?per_page=100"
            response = requests.get(url, headers=cls.get_headers(token))
            
            if response.status_code == 403 and 'rate limit' in response.text.lower():
                sync_run.status = 'RATE_LIMITED'
                sync_run.error_code = 'RATE_LIMIT_EXCEEDED'
                sync_run.completed_at = timezone.now()
                sync_run.save()
                return sync_run
                
            response.raise_for_status()
            repos_data = response.json()
            
            discovered = 0
            updated = 0
            
            for repo_data in repos_data:
                # Update or create the candidate repository
                repo, created = CandidateRepository.objects.update_or_create(
                    user=connection.user,
                    github_connection=connection,
                    external_repository_id=str(repo_data.get('id')),
                    defaults={
                        'name': repo_data.get('name', ''),
                        'full_name': repo_data.get('full_name', ''),
                        'description': repo_data.get('description', ''),
                        'repository_url': repo_data.get('html_url', ''),
                        'homepage_url': repo_data.get('homepage', ''),
                        'default_branch': repo_data.get('default_branch', 'main'),
                        'visibility': repo_data.get('visibility', 'public'),
                        'is_fork': repo_data.get('fork', False),
                        'is_archived': repo_data.get('archived', False),
                        'is_template': repo_data.get('is_template', False),
                        'is_private': repo_data.get('private', False),
                        'stars': repo_data.get('stargazers_count', 0),
                        'forks': repo_data.get('forks_count', 0),
                        'watchers': repo_data.get('watchers_count', 0),
                        'open_issues': repo_data.get('open_issues_count', 0),
                        'primary_language': repo_data.get('language', ''),
                        'repository_topics': repo_data.get('topics', []),
                        'raw_metadata_snapshot': repo_data
                    }
                )
                
                if created:
                    discovered += 1
                else:
                    updated += 1
                
                # Now extract evidence from this repository
                cls._extract_evidence_from_repo(connection.user, repo)
                
            sync_run.repositories_discovered = discovered
            sync_run.repositories_updated = updated
            sync_run.status = 'COMPLETED'
            
        except requests.exceptions.RequestException as e:
            sync_run.status = 'FAILED'
            sync_run.error_code = 'NETWORK_ERROR'
            sync_run.error_message = str(e)
            
        sync_run.completed_at = timezone.now()
        sync_run.save()
        
        connection.last_synced_at = timezone.now()
        connection.sync_status = sync_run.status
        if sync_run.status == 'FAILED':
            connection.sync_error_code = sync_run.error_code
        connection.save()
        
        return sync_run

    @classmethod
    def _extract_evidence_from_repo(cls, user, repo: CandidateRepository):
        """
        Extracts evidence securely from a repository's metadata.
        This relies on determinism and taxonomy.
        """
        # 1. Primary Language Evidence
        if repo.primary_language:
            cls._create_evidence(user, repo, repo.primary_language, 'LANGUAGE_STATISTICS')
            
        # 2. Topic Evidence
        for topic in repo.repository_topics:
            cls._create_evidence(user, repo, topic, 'REPOSITORY_TOPIC')
            
        # Optional: Further extraction could fetch contents like Dockerfile, package.json etc.
        # But this must be done safely without executing arbitrary code and observing rate limits.

    @classmethod
    def _create_evidence(cls, user, repo: CandidateRepository, raw_skill_name: str, evidence_type: str):
        # Normalize the raw skill
        canonical_name = SkillRequirementNormalizationService.normalize_skill(raw_skill_name)
        
        # We only record evidence for skills in our taxonomy or we create it
        taxonomy, _ = SkillTaxonomy.objects.get_or_create(
            canonical_name=canonical_name,
            defaults={'slug': canonical_name.lower()}
        )
        
        # Record the evidence idempotently
        CandidateSkillEvidence.objects.update_or_create(
            user=user,
            skill_taxonomy=taxonomy,
            repository=repo,
            source_type='GITHUB',
            evidence_type=evidence_type,
            defaults={
                'confidence': 'HIGH' if evidence_type == 'LANGUAGE_STATISTICS' else 'MEDIUM',
                'status': 'DETECTED',
                'evidence_summary': f"Detected via {evidence_type.lower().replace('_', ' ')} in repository {repo.name}."
            }
        )

class CandidateEvidenceAggregationService:
    """
    Aggregates disparate pieces of evidence to present a unified suggestion.
    """
    @staticmethod
    def get_user_evidence_summary(user) -> Dict[str, Any]:
        evidence_qs = CandidateSkillEvidence.objects.filter(user=user, status='DETECTED').select_related('skill_taxonomy')
        
        aggregated = {}
        for ev in evidence_qs:
            skill = ev.skill_taxonomy.canonical_name
            if skill not in aggregated:
                aggregated[skill] = {
                    'evidence_count': 0,
                    'sources': set(),
                    'evidence_items': []
                }
            
            aggregated[skill]['evidence_count'] += 1
            aggregated[skill]['sources'].add(ev.source_type)
            aggregated[skill]['evidence_items'].append({
                'id': ev.id,
                'source': ev.source_type,
                'type': ev.evidence_type,
                'repository': ev.repository.name if ev.repository else None,
                'portfolio_project': ev.portfolio_project.title if ev.portfolio_project else None,
            })
            
        # Convert sets to lists
        for skill in aggregated:
            aggregated[skill]['sources'] = list(aggregated[skill]['sources'])
            
        return aggregated

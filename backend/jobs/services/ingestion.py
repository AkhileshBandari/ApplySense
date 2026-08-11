import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from jobs.models import Job, JobRequirement
from ai_engine.fallback_manager import AIFallbackManager
from ai_engine import prompts

logger = logging.getLogger(__name__)

class JobValidationService:
    @staticmethod
    def validate(normalized_data: Dict[str, Any]) -> bool:
        if not normalized_data.get('title') or not normalized_data.get('company'):
            return False
        if not normalized_data.get('description') or len(normalized_data['description']) < 50:
            return False
        return True


class SkillNormalizationService:
    # A basic canonical mapping. In a real production system, this could be backed by a DB or external ontology.
    CANONICAL_MAP = {
        "reactjs": "React",
        "react.js": "React",
        "react": "React",
        "vuejs": "Vue",
        "vue.js": "Vue",
        "vue": "Vue",
        "node.js": "Node.js",
        "nodejs": "Node.js",
        "node": "Node.js",
        "python3": "Python",
        "python": "Python",
        "golang": "Go",
        "go": "Go",
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "aws": "AWS",
        "amazon web services": "AWS",
        "gcp": "Google Cloud",
        "google cloud platform": "Google Cloud",
        "k8s": "Kubernetes",
        "kubernetes": "Kubernetes",
    }

    @classmethod
    def normalize(cls, skill: str) -> str:
        s = skill.lower().strip()
        return cls.CANONICAL_MAP.get(s, skill.title())


class JobNormalizationService:
    def __init__(self):
        self.ai_manager = AIFallbackManager()

    def process(self, raw_job: Dict[str, Any]) -> Job:
        """Process normalized raw_job dict into a saved Job and JobRequirement."""
        
        # Determine unique fields
        title = raw_job.get("title", "").strip()
        company = raw_job.get("company", "").strip()
        location = raw_job.get("location", "").strip()
        source_url = raw_job.get("source_url")
        source_job_id = raw_job.get("source_job_id")
        
        # Check if exists to avoid duplication
        job = JobDeduplicationService.find_exact_duplicate(source_url, source_job_id, company, title, location)
        
        if not job:
            job = Job(
                title=title,
                company=company,
                location=location,
                work_mode=raw_job.get("work_mode"),
                portal_type=raw_job.get("portal_type", "Custom"),
                source_url=source_url,
                source_job_id=source_job_id,
                description=raw_job.get("description", ""),
            )
            job.save()

        self._extract_and_save_requirements(job)
        return job

    def _extract_and_save_requirements(self, job: Job):
        if hasattr(job, 'requirements_norm'):
            return # Already extracted
            
        try:
            # We use AI to extract requirements reliably from unstructured descriptions
            response = self.ai_manager.run_prompt(
                prompts.JOB_REQUIREMENT_EXTRACTION_PROMPT,
                {"job_description": job.description}
            )
            
            # Normalize extracted skills
            req_skills = [SkillNormalizationService.normalize(s) for s in response.get("required_skills", [])]
            pref_skills = [SkillNormalizationService.normalize(s) for s in response.get("preferred_skills", [])]
            
            JobRequirement.objects.create(
                job=job,
                required_skills=list(set(req_skills)),
                preferred_skills=list(set(pref_skills)),
                minimum_experience=response.get("minimum_experience_years") or 0,
                education_requirements=response.get("education", []),
                responsibilities=response.get("responsibilities", [])
            )
        except Exception as e:
            logger.error(f"Failed to extract requirements for job {job.id}: {e}")
            # Fallback to empty requirements
            JobRequirement.objects.create(
                job=job,
                required_skills=[],
                preferred_skills=[],
                minimum_experience=0,
                education_requirements=[],
                responsibilities=[]
            )


class JobDeduplicationService:
    @staticmethod
    def find_exact_duplicate(source_url: str, source_job_id: str, company: str, title: str, location: str) -> Optional[Job]:
        if source_url:
            job = Job.objects.filter(source_url=source_url).first()
            if job: return job
            
        if source_job_id and company:
            job = Job.objects.filter(source_job_id=source_job_id, company=company).first()
            if job: return job
            
        # Heuristic fallback
        if company and title:
            job = Job.objects.filter(company=company, title=title, location=location).first()
            if job: return job
            
        return None


class JobFreshnessService:
    @staticmethod
    def update_freshness():
        now = timezone.now()
        stale_threshold = now - timedelta(days=30)
        closed_threshold = now - timedelta(days=60)
        
        Job.objects.filter(
            status='ACTIVE', last_seen_at__lt=stale_threshold
        ).update(status='STALE')
        
        Job.objects.filter(
            status__in=['ACTIVE', 'STALE'], last_seen_at__lt=closed_threshold
        ).update(status='CLOSED')

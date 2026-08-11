import json
import logging
from django.utils import timezone
from resumes.models import Resume, ResumeVersion, TailoringChange
from jobs.models import Job
from profiles.services.candidate_context import CandidateContextService
from jobs.services.job_normalization import JobNormalizationService
from resumes.services.claim_validation import ClaimValidationService
from ai_engine.fallback_manager import AIFallbackManager

logger = logging.getLogger(__name__)

TAILORING_PROMPT = """You are an expert resume writer.
Tailor the candidate's resume for the specific job description by rewriting bullets for clarity, impact, and relevance.

You are given:
1. Candidate Verified Evidence: The verified profile facts.
2. Original Resume: The parsed resume JSON.
3. Job Requirements: The normalized job requirements.

Propose changes to the resume content to better align with the job requirements.
DO NOT invent any new facts, metrics, or skills that are not in the verified evidence.

Return a strictly formatted JSON array of proposed changes with this schema:
[
  {
    "section": "experience",
    "original_text": "Built APIs using Python.",
    "proposed_text": "Designed and developed scalable REST APIs using Python and Django to support microservices.",
    "reason": "Aligns with the job requirement for REST API development."
  }
]
Do not include markdown blocks. Only output raw JSON array.
"""

class ResumeTailoringService:
    @staticmethod
    def generate_tailored_version(resume: Resume, job: Job) -> ResumeVersion:
        user = resume.user
        
        # 1. Get Context and Job Reqs
        context_service = CandidateContextService()
        verified_context = context_service.get_for_user(user)
        verified_context_json = json.dumps(verified_context, default=str)

        reqs = JobNormalizationService.normalize_job(job)
        reqs_json = json.dumps({
            "required_skills": reqs.required_skills,
            "preferred_skills": reqs.preferred_skills,
            "responsibilities": reqs.responsibilities
        })
        
        original_resume_json = json.dumps(resume.parsed_data or {})

        # 2. Ask LLM for proposed changes
        ai = AIFallbackManager()
        proposed_changes = []
        try:
            response = ai.generate_content(
                system_prompt=TAILORING_PROMPT,
                user_prompt=f"VERIFIED EVIDENCE:\n{verified_context_json}\n\nORIGINAL RESUME:\n{original_resume_json}\n\nJOB REQUIREMENTS:\n{reqs_json}",
                response_format_json=True
            )
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            proposed_changes = json.loads(cleaned.strip())
        except Exception as e:
            logger.error(f"Tailoring generation failed: {str(e)}")
            raise ValueError("Failed to generate tailoring suggestions.")

        # 3. Create Draft ResumeVersion
        version_name = f"Tailored for {job.company} - {timezone.now().strftime('%Y-%m-%d')}"
        version = ResumeVersion.objects.create(
            user=user,
            source_resume=resume,
            target_job=job,
            version_name=version_name,
            structured_content=resume.parsed_data or {}, # Base content
            status='DRAFT'
        )

        # 4. Process and Validate each proposed change
        for change in proposed_changes:
            original_text = change.get("original_text", "")
            proposed_text = change.get("proposed_text", "")
            reason = change.get("reason", "")
            section = change.get("section", "general")

            if not proposed_text:
                continue

            # CLAIM VALIDATION: Mandatory safety layer
            validation_status = ClaimValidationService.validate_claim(
                verified_evidence_text=verified_context_json,
                proposed_claim=proposed_text
            )

            # Auto-reject unsupported claims
            if validation_status == "UNSUPPORTED":
                logger.warning(f"Rejected unsupported claim: {proposed_text}")
                continue
            
            # Save the proposed change
            TailoringChange.objects.create(
                version=version,
                section=section,
                original_text=original_text,
                proposed_text=proposed_text,
                reason=reason,
                validation_status=validation_status,
                user_decision='PENDING' if validation_status == 'AMBIGUOUS' else 'ACCEPTED' 
                # Wait, better require user to explicitly accept all, or just leave pending
            )
            
            # Let's default all to PENDING to ensure user review
            TailoringChange.objects.filter(id=TailoringChange.objects.latest('id').id).update(user_decision='PENDING')

        return version

    @staticmethod
    def approve_version(version: ResumeVersion) -> ResumeVersion:
        """
        Approve the version, applying all ACCEPTED changes to the structured_content.
        """
        # For simplicity, we just mark it approved. 
        # In a fully robust system, we would walk the JSON tree and replace `original_text` with `proposed_text`
        # for all ACCEPTED changes.
        changes = version.changes.filter(user_decision='ACCEPTED')
        content_str = json.dumps(version.structured_content)
        
        for change in changes:
            if change.original_text and change.original_text in content_str:
                content_str = content_str.replace(change.original_text, change.proposed_text)
                
        version.structured_content = json.loads(content_str)
        version.status = 'APPROVED'
        version.save()
        return version

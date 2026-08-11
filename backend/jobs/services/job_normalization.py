import json
import logging
from jobs.models import Job, JobRequirement
from ai_engine.fallback_manager import AIFallbackManager

logger = logging.getLogger(__name__)

JOB_NORMALIZATION_PROMPT = """You are an expert technical recruiter and job analyst.
Extract and normalize the requirements from the following job description.

Extract the information into the following JSON schema strictly:
{
    "required_skills": ["skill1", "skill2"], // Essential skills stated as requirements
    "preferred_skills": ["skill3", "skill4"], // Nice to have, plus, or preferred skills
    "minimum_experience": 5, // The minimum years of experience required (integer). If not stated, return null.
    "education_requirements": ["Bachelors in CS", "Masters"], // Degree requirements
    "responsibilities": ["Develop REST APIs", "Mentor junior devs"] // Key responsibilities
}

Respond ONLY with valid JSON. Do not include markdown code block wrappers (e.g. ```json). Just the raw JSON object.
"""

class JobNormalizationService:
    @staticmethod
    def normalize_job(job: Job) -> JobRequirement:
        # Check if already normalized
        if hasattr(job, 'requirements_norm'):
            return job.requirements_norm

        ai = AIFallbackManager()
        
        try:
            response = ai.generate_content(
                system_prompt=JOB_NORMALIZATION_PROMPT,
                user_prompt=f"Job Title: {job.title}\nCompany: {job.company}\nDescription:\n{job.description}",
                response_format_json=True
            )
            
            # Clean response if it contains markdown
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            parsed = json.loads(cleaned)
            
            req = JobRequirement.objects.create(
                job=job,
                required_skills=parsed.get('required_skills', []),
                preferred_skills=parsed.get('preferred_skills', []),
                minimum_experience=parsed.get('minimum_experience'),
                education_requirements=parsed.get('education_requirements', []),
                responsibilities=parsed.get('responsibilities', [])
            )
            return req
            
        except Exception as e:
            logger.error(f"Failed to normalize job {job.id}: {str(e)}")
            # Return an empty requirement set gracefully if AI fails
            return JobRequirement.objects.create(job=job)

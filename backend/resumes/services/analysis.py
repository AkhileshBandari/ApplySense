import logging
import json
from resumes.models import Resume, ResumeAnalysis
from jobs.models import Job
from profiles.services.candidate_context import CandidateContextService
from resumes.services.scoring import ResumeScoringService
from jobs.services.job_normalization import JobNormalizationService
from ai_engine.fallback_manager import AIFallbackManager

logger = logging.getLogger(__name__)

QUALITATIVE_ANALYSIS_PROMPT = """You are an expert resume writer. Provide qualitative analysis on the candidate's resume.
Focus on bullet clarity, weak/vague wording, and impact.
Return a strictly formatted JSON array of dictionaries with the schema:
[
  {
    "section": "experience",
    "issue": "Vague wording in bullet 'Did some stuff'",
    "recommendation": "Use strong action verbs like 'Architected' or 'Developed'"
  }
]
Do not include markdown blocks. Only output raw JSON.
"""

JOB_SPECIFIC_MATCH_PROMPT = """You are an expert technical recruiter matching a candidate against a job description.
Evaluate the candidate's verified evidence against the normalized job requirements.
Return a strict JSON object with this schema:
{
    "strong_matches": ["skill1", "skill2"],
    "partial_matches": ["skill3"],
    "missing_requirements": ["skill4", "skill5"],
    "hard_gaps": ["Missing 2 years of required experience"],
    "recommendations": ["Highlight your work with React more prominently"]
}
Do not include markdown blocks. Only output raw JSON.
"""

class ResumeAnalysisService:
    @staticmethod
    def analyze_general(resume: Resume) -> ResumeAnalysis:
        # Deterministic general scoring
        parsed = resume.parsed_data or {}
        scoring = ResumeScoringService.calculate_general_score(parsed, resume.parsed_text)
        
        # Optional AI Qualitative Analysis
        ai = AIFallbackManager()
        qualitative_feedback = []
        try:
            response = ai.generate_content(
                system_prompt=QUALITATIVE_ANALYSIS_PROMPT,
                user_prompt=f"Resume Text:\n{resume.parsed_text}",
                response_format_json=True
            )
            
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            qualitative_feedback = json.loads(cleaned.strip())
        except Exception as e:
            logger.warning(f"AI qualitative analysis failed: {str(e)}")
            qualitative_feedback = [{"issue": "AI qualitative analysis unavailable", "recommendation": "Try again later."}]

        structured_results = {
            "dimensions": scoring["dimensions"],
            "issues": scoring["issues"],
            "qualitative": qualitative_feedback
        }

        analysis = ResumeAnalysis.objects.create(
            user=resume.user,
            resume=resume,
            analysis_type='GENERAL',
            overall_score=scoring["overall_score"],
            calculation_version=scoring["calculation_version"],
            structured_results=structured_results
        )
        return analysis

    @staticmethod
    def analyze_job_specific(resume: Resume, job: Job) -> ResumeAnalysis:
        # 1. Get Verified Context
        context_service = CandidateContextService()
        verified_context = context_service.get_for_user(resume.user)
        context_json = json.dumps(verified_context, default=str)

        # 2. Get Normalized Job Requirements
        reqs = JobNormalizationService.normalize_job(job)
        reqs_json = json.dumps({
            "required_skills": reqs.required_skills,
            "preferred_skills": reqs.preferred_skills,
            "minimum_experience": reqs.minimum_experience,
            "education_requirements": reqs.education_requirements,
            "responsibilities": reqs.responsibilities
        })

        # 3. Match Context to Requirements (AI-based Job Specific Analysis)
        ai = AIFallbackManager()
        structured_results = {
            "strong_matches": [],
            "partial_matches": [],
            "missing_requirements": [],
            "hard_gaps": [],
            "recommendations": []
        }
        score = 0
        try:
            response = ai.generate_content(
                system_prompt=JOB_SPECIFIC_MATCH_PROMPT,
                user_prompt=f"CANDIDATE VERIFIED EVIDENCE:\n{context_json}\n\nJOB REQUIREMENTS:\n{reqs_json}",
                response_format_json=True
            )
            
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.replace("```json", "", 1)
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
                
            structured_results = json.loads(cleaned.strip())
            
            # Simple heuristic score based on missing vs strong matches
            matches_count = len(structured_results.get("strong_matches", []))
            missing_count = len(structured_results.get("missing_requirements", []))
            hard_gaps = len(structured_results.get("hard_gaps", []))
            
            base = 50
            base += (matches_count * 5)
            base -= (missing_count * 10)
            base -= (hard_gaps * 20)
            score = max(0, min(100, base))
            
        except Exception as e:
            logger.error(f"Job specific analysis failed: {str(e)}")
            structured_results["error"] = "AI Analysis failed to complete."
            score = 0

        analysis = ResumeAnalysis.objects.create(
            user=resume.user,
            resume=resume,
            target_job=job,
            analysis_type='JOB_SPECIFIC',
            overall_score=score,
            calculation_version="v1.0",
            structured_results=structured_results
        )
        return analysis

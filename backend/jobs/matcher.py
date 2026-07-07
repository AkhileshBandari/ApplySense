import re
import json
import logging
from datetime import date
from django.conf import settings
from ai_engine.fallback_manager import AIFallbackManager
from ai_engine import prompts
from profiles.models import Profile

logger = logging.getLogger(__name__)


def parse_experience_years_required(job_desc: str) -> int:
    """Extract numerical experience requirement from job description.
    Supports patterns like '5+ years', '3-5 years', 'at least 8 years'."""
    match = re.search(r"(\d+)\+?\s*years?", job_desc, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0


def calculate_candidate_experience_years(profile: Profile) -> float:
    """Calculate total years of experience from a user's profile."""
    total_days = 0
    for exp in profile.experiences.all():
        start = exp.start_date or date.today()
        end = date.today() if exp.is_current or not exp.end_date else exp.end_date
        total_days += (end - start).days
    return round(total_days / 365.0, 1)


def _extract_tech_keywords(resume_text: str) -> set:
    """Simple keyword extraction from raw resume text using a predefined list."""
    tech_keywords = {
        "python",
        "django",
        "react",
        "typescript",
        "javascript",
        "html",
        "css",
        "sql",
        "postgresql",
        "aws",
        "docker",
        "kubernetes",
        "git",
        "rest",
        "graphql",
        "node",
        "express",
        "vue",
        "angular",
        "java",
        "c#",
        "c++",
        "go",
        "ruby",
        "php",
        "linux",
        "ubuntu",
        "azure",
    }
    words = set(re.findall(r"[a-zA-Z#]+", resume_text.lower()))
    return tech_keywords.intersection(words)


def match_resume_to_job(resume_text: str, job_desc: str, profile: Profile = None) -> dict:
    """Composite matching algorithm that combines heuristic rules with optional AI fallback.

    Returns a dictionary with a numeric ``score`` (0‑100) and a ``details`` sub‑dict.
    """
    # Base heuristic score
    rule_score = 50
    details = {"experience": None, "skills": None, "fallback": None}

    # 1️⃣ Experience matching
    req_years = parse_experience_years_required(job_desc)
    cand_years = calculate_candidate_experience_years(profile) if profile else 0.0
    details["experience"] = {"required": req_years, "candidate": cand_years}
    if req_years > 0:
        if cand_years >= req_years:
            rule_score += 15
        elif cand_years >= (req_years - 2):
            rule_score += 5
        else:
            rule_score -= 10

    # 2️⃣ Skill overlap
    if profile:
        skills = [s.name.lower() for s in profile.skills.all()]
        skill_set = set(skills)
    else:
        # Fallback: extract keywords directly from resume text
        skill_set = _extract_tech_keywords(resume_text)
    # Compare with a predefined tech list
    common = skill_set & {
        "python",
        "django",
        "react",
        "typescript",
        "javascript",
        "html",
        "css",
        "sql",
        "aws",
        "docker",
    }
    skill_score = len(common) * 5  # each matching skill contributes 5 points
    rule_score += skill_score
    details["skills"] = {"matched": list(common), "count": len(common)}

    # 3️⃣ AI fallback (optional, only when profile is missing)
    if not profile:
        try:
            fallback = AIFallbackManager()
            ai_response = fallback.run_prompt(prompts.MATCH_RESUME_TO_JOB, {
                "resume": resume_text,
                "job_description": job_desc,
            })
            details["fallback"] = ai_response
        except Exception as exc:  # pragma: no cover – defensive
            logger.exception("AI fallback failed: %s", exc)
            details["fallback"] = {"error": str(exc)}

    # Clamp score to 0‑100 range
    final_score = max(0, min(100, rule_score))
    return {"score": final_score, "details": details}

from profiles.models import (
    Profile, Experience, Education, Skill, Project, 
    Certification, Achievement, Language, CareerPreferences, WorkAuthorization, VerificationStatus
)

class CandidateContextService:
    @staticmethod
    def get_for_user(user) -> dict:
        """
        Returns only the VERIFIED candidate context for downstream AI applications.
        """
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            return {}

        def get_verified(queryset):
            return queryset.filter(verification_status=VerificationStatus.VERIFIED)

        context = {
            "professional_profile": {
                "name": profile.name,
                "headline": profile.professional_headline,
                "summary": profile.bio,
                "location": profile.location,
                "experience_level": profile.experience_level,
                "career_goals": profile.career_goals,
            },
            "contact": {
                "phone": profile.phone,
                "email": user.email,
                "linkedin": profile.linkedin_url,
                "github": profile.github_url,
                "portfolio": profile.portfolio_url,
            },
            "experience": [
                {
                    "company": exp.company,
                    "role": exp.role,
                    "location": exp.location,
                    "start_date": exp.start_date.isoformat() if exp.start_date else None,
                    "end_date": exp.end_date.isoformat() if exp.end_date else None,
                    "is_current": exp.is_current,
                    "description": exp.description,
                }
                for exp in get_verified(profile.experiences)
            ],
            "education": [
                {
                    "institution": edu.institution,
                    "degree": edu.degree,
                    "field_of_study": edu.field_of_study,
                    "start_date": edu.start_date.isoformat() if edu.start_date else None,
                    "end_date": edu.end_date.isoformat() if edu.end_date else None,
                    "grade": edu.grade,
                }
                for edu in get_verified(profile.educations)
            ],
            "skills": [
                {
                    "name": skill.name,
                    "category": skill.category,
                }
                for skill in get_verified(profile.skills)
            ],
            "projects": [
                {
                    "name": proj.name,
                    "description": proj.description,
                    "technologies": proj.technologies,
                    "link": proj.link,
                }
                for proj in get_verified(profile.projects)
            ],
            "certifications": [
                {
                    "name": cert.name,
                    "issuer": cert.issuing_organization,
                    "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
                    "url": cert.credential_url,
                }
                for cert in get_verified(profile.certifications)
            ],
            "languages": [
                {"name": lang.name, "proficiency": lang.proficiency}
                for lang in get_verified(profile.languages)
            ]
        }
        
        # Add preferences and auth if they exist and are verified
        try:
            pref = profile.preferences
            if getattr(pref, 'verification_status', VerificationStatus.VERIFIED) == VerificationStatus.VERIFIED:
                context["preferences"] = {
                    "roles": pref.preferred_roles,
                    "locations": pref.preferred_locations,
                    "industries": pref.preferred_industries,
                    "job_type": pref.job_type,
                    "remote": pref.remote_preference,
                    "relocation_willingness": pref.relocation_willingness,
                    "currency": pref.currency,
                }
        except CareerPreferences.DoesNotExist:
            pass

        context["work_authorizations"] = [
            {
                "country": wa.country,
                "status": wa.status,
                "sponsorship_required": wa.sponsorship_required
            }
            for wa in get_verified(profile.work_authorizations)
        ]

        return context

    @staticmethod
    def calculate_completeness(user) -> dict:
        """
        Deterministic completeness calculation.
        """
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            return {"overall": 0, "missing": ["Profile"]}

        weights = {
            "headline": 5,
            "summary": 10,
            "experience": 30,
            "education": 20,
            "skills": 20,
            "contact_links": 15,
        }

        score = 0
        missing = []
        
        # Headline
        if profile.professional_headline:
            score += weights["headline"]
        else:
            missing.append("Professional Headline")
            
        # Summary
        if profile.bio:
            score += weights["summary"]
        else:
            missing.append("Summary / Bio")
            
        # Experience
        # Fresher logic: if experience is missing but projects exist, substitute the weight.
        verified_exp = profile.experiences.filter(verification_status=VerificationStatus.VERIFIED).count()
        verified_proj = profile.projects.filter(verification_status=VerificationStatus.VERIFIED).count()
        if verified_exp > 0:
            score += weights["experience"]
        elif verified_proj > 0:
            score += weights["experience"] # Substitute weight for freshers with projects
        else:
            missing.append("Experience or Projects")

        # Education
        if profile.educations.filter(verification_status=VerificationStatus.VERIFIED).count() > 0:
            score += weights["education"]
        else:
            missing.append("Education")

        # Skills
        if profile.skills.filter(verification_status=VerificationStatus.VERIFIED).count() >= 3:
            score += weights["skills"]
        else:
            missing.append("At least 3 Skills")

        # Links
        if profile.linkedin_url or profile.github_url or profile.portfolio_url:
            score += weights["contact_links"]
        else:
            missing.append("Professional Links (LinkedIn, GitHub, etc.)")

        return {
            "overall": score,
            "missing": missing,
            "next_action": missing[0] if missing else "Keep your profile up to date!"
        }

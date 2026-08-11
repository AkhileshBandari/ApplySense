from django.db import transaction
from profiles.models import (
    Profile, Experience, Education, Skill, Project, 
    Certification, Achievement, Language, ProvenanceSource, VerificationStatus
)

class ProvenanceService:
    @staticmethod
    @transaction.atomic
    def import_parsed_resume(user, resume, parsed_data: dict):
        """
        Takes validated JSON and creates UNVERIFIED facts on the user's Profile.
        Returns the lists of created facts.
        """
        profile = user.profile
        
        # We do not overwrite the main Profile fields automatically, 
        # but we can return them for comparison later if needed.
        
        created_records = {
            "experiences": [],
            "educations": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "achievements": [],
            "languages": [],
        }

        # Insert Experiences
        for exp in parsed_data.get("experience", []):
            created_records["experiences"].append(
                Experience.objects.create(
                    profile=profile,
                    company=exp.get("company", "")[:150],
                    role=exp.get("role", "")[:150],
                    location=exp.get("location", "")[:150],
                    start_date=exp.get("start_date") if exp.get("start_date") else None, # Needs parsing in real life
                    end_date=exp.get("end_date") if exp.get("end_date") else None,
                    is_current=exp.get("current", False),
                    description="\n".join(exp.get("bullets", [])),
                    source=ProvenanceSource.RESUME_IMPORTED,
                    verification_status=VerificationStatus.UNVERIFIED,
                    source_resume=resume
                )
            )

        # Insert Educations
        for edu in parsed_data.get("education", []):
            created_records["educations"].append(
                Education.objects.create(
                    profile=profile,
                    institution=edu.get("institution", "")[:150],
                    degree=edu.get("degree", "")[:100],
                    field_of_study=edu.get("field", "")[:150],
                    # start_date and end_date skipped for simplicity unless they map properly
                    grade=edu.get("grade", "")[:50],
                    source=ProvenanceSource.RESUME_IMPORTED,
                    verification_status=VerificationStatus.UNVERIFIED,
                    source_resume=resume
                )
            )

        # Insert Skills
        for skill in parsed_data.get("skills", []):
            # API might return a list of dicts or list of strings depending on prompt
            skill_name = skill.get("name", "")[:100] if isinstance(skill, dict) else str(skill)[:100]
            skill_cat = skill.get("category", "")[:100] if isinstance(skill, dict) else ""
            if skill_name:
                created_records["skills"].append(
                    Skill.objects.create(
                        profile=profile,
                        name=skill_name,
                        category=skill_cat,
                        source=ProvenanceSource.RESUME_IMPORTED,
                        verification_status=VerificationStatus.UNVERIFIED,
                        source_resume=resume
                    )
                )

        # Insert Projects
        for proj in parsed_data.get("projects", []):
            created_records["projects"].append(
                Project.objects.create(
                    profile=profile,
                    name=proj.get("name", "")[:150],
                    description=proj.get("description", "") + "\n" + "\n".join(proj.get("bullets", [])),
                    technologies=", ".join(proj.get("technologies", []))[:255],
                    link=(proj.get("links", []) + [""])[0][:200], # basic list extract
                    source=ProvenanceSource.RESUME_IMPORTED,
                    verification_status=VerificationStatus.UNVERIFIED,
                    source_resume=resume
                )
            )

        # Insert Certifications
        for cert in parsed_data.get("certifications", []):
            created_records["certifications"].append(
                Certification.objects.create(
                    profile=profile,
                    name=cert.get("name", "")[:150],
                    issuing_organization=cert.get("issuer", "")[:150],
                    source=ProvenanceSource.RESUME_IMPORTED,
                    verification_status=VerificationStatus.UNVERIFIED,
                    source_resume=resume
                )
            )

        return created_records

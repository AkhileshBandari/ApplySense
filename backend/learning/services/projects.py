from typing import List
from learning.models import SkillGapAnalysis, ProjectRecommendation, GapType

class ProjectRecommendationService:
    @staticmethod
    def generate_recommendations(analysis: SkillGapAnalysis) -> List[ProjectRecommendation]:
        # Identify gaps that need evidence
        target_skills = []
        for gap in analysis.gap_items.all():
            if gap.gap_type in [GapType.EVIDENCE_GAP, GapType.MISSING_SKILL, GapType.EXPERIENCE_GAP]:
                target_skills.append(gap.canonical_skill)
                
        if not target_skills:
            return []
            
        # Instead of hallucinating, we use deterministic project templates
        # mapped to combinations of skills.
        
        recs = []
        if "React" in target_skills and "Django" in target_skills:
            recs.append(ProjectRecommendation.objects.create(
                user=analysis.user,
                analysis=analysis,
                title="Fullstack Task Management System",
                description="Build a production-ready API in Django with a React frontend.",
                target_skills=["React", "Django", "REST APIs"],
                estimated_effort_hours=40,
                deliverables=["React SPA", "Django REST API", "Authentication"],
                success_criteria=["Must handle 1000 req/sec", "Must have 80% test coverage"]
            ))
        elif "Docker" in target_skills or "Kubernetes" in target_skills:
            recs.append(ProjectRecommendation.objects.create(
                user=analysis.user,
                analysis=analysis,
                title="Containerized Microservices Cluster",
                description="Deploy a set of microservices using Docker and Kubernetes.",
                target_skills=["Docker", "Kubernetes", "Linux"],
                estimated_effort_hours=30,
                deliverables=["Dockerfile", "k8s deployment yaml"],
                success_criteria=["Services communicate over internal network"]
            ))
        else:
            # Generic fallback project addressing the top skill
            top_skill = target_skills[0]
            recs.append(ProjectRecommendation.objects.create(
                user=analysis.user,
                analysis=analysis,
                title=f"Advanced {top_skill} Implementation",
                description=f"Build a deep dive project showcasing {top_skill} capabilities.",
                target_skills=[top_skill],
                estimated_effort_hours=20,
                deliverables=["Source Code", "Documentation"],
                success_criteria=["Implements advanced patterns"]
            ))
            
        return recs

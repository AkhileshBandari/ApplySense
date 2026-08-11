from interviews.models import InterviewWeakness, InterviewImprovementPlan
from django.db.models import Avg, Count
from ai_engine.fallback_manager import AIFallbackManager
import json

class InterviewReadinessService:
    @staticmethod
    def calculate_readiness(user):
        """
        Calculate bounded readiness score based on completed mock sessions.
        Returns 'INSUFFICIENT_INTERVIEW_DATA' if < 2 sessions.
        """
        completed_sessions = user.mock_sessions.filter(status='COMPLETED')
        if completed_sessions.count() < 2:
            return "INSUFFICIENT_INTERVIEW_DATA"
            
        avg_score = completed_sessions.aggregate(Avg('overall_readiness_score'))['overall_readiness_score__avg']
        if avg_score is None:
            return "INSUFFICIENT_INTERVIEW_DATA"
            
        return int(avg_score)

class InterviewWeaknessService:
    @staticmethod
    def extract_weaknesses(session):
        """
        Aggregates weaknesses from response evaluations in a session.
        """
        evals = [resp.evaluation for resp in session.questions.filter(responses__evaluation__isnull=False).distinct()]
        
        weaknesses_list = []
        for e in evals:
            if hasattr(e, 'weaknesses') and e.weaknesses:
                weaknesses_list.extend(e.weaknesses)
            if hasattr(e, 'missing_concepts') and e.missing_concepts:
                weaknesses_list.extend(e.missing_concepts)
                
        # Count frequency to determine severity
        from collections import Counter
        freq = Counter(weaknesses_list)
        
        for w, count in freq.items():
            if count >= 2:
                severity = 'HIGH'
            else:
                severity = 'MEDIUM'
                
            InterviewWeakness.objects.create(
                user=session.user,
                session=session,
                category='GENERAL',
                skill=w,
                severity=severity,
                reason_code='REPEATED_MISSING_CONCEPT' if count >=2 else 'ONE_OFF_WEAKNESS',
                status='IDENTIFIED'
            )

from learning.models import LearningRoadmap, LearningRoadmapItem, PriorityBand

class InterviewImprovementPlanService:
    @staticmethod
    def generate_plan(session):
        """
        Generates an improvement plan based on the session's weaknesses.
        """
        weaknesses = session.weaknesses.all()
        if not weaknesses.exists():
            return None
            
        plan_content = {
            "focus_areas": [],
            "recommended_actions": []
        }
        
        # Look for active roadmap
        active_roadmap = LearningRoadmap.objects.filter(user=session.user, is_stale=False).order_by('-created_at').first()
        
        for w in weaknesses:
            plan_content["focus_areas"].append(w.skill)
            if w.severity in ['HIGH', 'CRITICAL']:
                plan_content["recommended_actions"].append(f"Review and practice deep dive on {w.skill}")
                
                # Push to Roadmap if it exists
                if active_roadmap and w.skill:
                    # check if it already exists
                    if not LearningRoadmapItem.objects.filter(roadmap=active_roadmap, canonical_skill=w.skill, status__in=['NOT_STARTED', 'IN_PROGRESS']).exists():
                        LearningRoadmapItem.objects.create(
                            roadmap=active_roadmap,
                            canonical_skill=w.skill,
                            title=f"Interview Weakness: {w.skill}",
                            objective=f"Improve performance on {w.skill} based on recent interview feedback.",
                            priority=PriorityBand.HIGH,
                            estimated_effort_hours=2.0
                        )
                
        # Generate the plan record
        plan = InterviewImprovementPlan.objects.create(
            user=session.user,
            session=session,
            structured_content=plan_content
        )
        return plan

from django.db.models import Prefetch
from career_pathways.models import (
    CareerPath, CareerPathRequirement, CareerPathScenario,
    AssumptionType, ScenarioStatus
)
from profiles.services.candidate_context import CandidateContextService
from learning.services.gap_analysis import SkillGapAnalysisService
from interviews.services.AnalyticsServices import InterviewReadinessService
import json
import logging

logger = logging.getLogger(__name__)

class CareerPathRecommendationService:
    """
    Ranks possible career paths using deterministic explainable dimensions.
    Outputs bounded readiness classifications, never LLM probability guesses.
    """
    @staticmethod
    def evaluate_paths_for_user(user):
        context = CandidateContextService.get_for_user(user)
        verified_skills_list = [s['name'] for s in context.get('skills', [])]
        
        # Base interview readiness
        interview_readiness = InterviewReadinessService.calculate_readiness(user)
        if isinstance(interview_readiness, str):
            interview_score = 0
        else:
            interview_score = interview_readiness
            
        # Get active paths
        paths = CareerPath.objects.filter(active=True).prefetch_related('requirements')
        
        recommendations = []
        for path in paths:
            reqs = path.requirements.all()
            total_reqs = reqs.count()
            
            if total_reqs == 0:
                continue
                
            matched_reqs = [r for r in reqs if r.canonical_skill in verified_skills_list]
            coverage = len(matched_reqs) / total_reqs
            
            # 1. Evidence Score (Based on verification status of matched skills)
            evidence_score = 0
            if total_reqs > 0:
                # All skills in CandidateContext are VERIFIED by definition.
                # However, if we were inspecting simulated contexts or deeper CandidateSkillEvidence,
                # we would differentiate here. For now, it matches coverage.
                evidence_score = int((len(matched_reqs) / total_reqs) * 100)
            
            # 2. Career Brand Score
            # Safely attempt to read from Phase 7D models if available
            brand_score = 0
            try:
                from career_brand.models import ProfessionalProfileAnalysis
                analysis = ProfessionalProfileAnalysis.objects.filter(profile__user=user).order_by('-created_at').first()
                if analysis:
                    brand_score = analysis.brand_readiness_score
            except Exception:
                pass
                
            # 3. Market Alignment
            market_alignment = "INSUFFICIENT_MARKET_DATA"
            try:
                from jobs.models import MarketSkillDemand
                demand = MarketSkillDemand.objects.filter(skill_name=path.canonical_role_name).first()
                if demand:
                    market_alignment = demand.demand_category
            except Exception:
                pass
            
            # Simple deterministic scoring (0-100) across all 4 dimensions
            skill_score = int(coverage * 100)
            
            overall_readiness = int((skill_score * 0.4) + (interview_score * 0.2) + (evidence_score * 0.2) + (brand_score * 0.2))
            
            if overall_readiness >= 80:
                classification = "READY"
                gap_level = "Low"
            elif overall_readiness >= 65:
                classification = "NEAR_READY"
                gap_level = "Low"
            elif overall_readiness >= 50:
                classification = "GAP_REDUCTION_REQUIRED"
                gap_level = "Medium"
            elif overall_readiness >= 30:
                classification = "SIGNIFICANT_GAP"
                gap_level = "High"
            else:
                classification = "CURRENTLY_MISALIGNED"
                gap_level = "High"
                
            recommendations.append({
                "path_id": path.id,
                "role_name": path.canonical_role_name,
                "overall_readiness": overall_readiness,
                "classification": classification,
                "gap_level": gap_level,
                "market_alignment": market_alignment,
                "skill_score": skill_score,
                "interview_score": interview_score,
                "evidence_score": evidence_score,
                "brand_score": brand_score
            })
            
        recommendations.sort(key=lambda x: x['overall_readiness'], reverse=True)
        return recommendations


class ScenarioSimulationEngine:
    """
    Engine to compute the simulated state strictly through isolated snapshots.
    NEVER mutates verified CandidateContext or real analytics.
    """
    @staticmethod
    def create_scenario(user, name, target_path_id=None, overrides=None):
        """Creates a new scenario with an immutable baseline snapshot."""
        overrides = overrides or {}
        
        baseline = CandidateContextService.get_for_user(user)
        # Append interview readiness to baseline snapshot
        baseline['interview_readiness'] = InterviewReadinessService.calculate_readiness(user)
        
        scenario = CareerPathScenario.objects.create(
            user=user,
            name=name,
            target_path_id=target_path_id,
            target_role=overrides.get('target_role', ''),
            target_country=overrides.get('target_country', ''),
            baseline_snapshot=baseline,
            simulated_snapshot=baseline # Initial state is identical
        )
        return scenario
        
    @staticmethod
    def simulate(scenario):
        """
        Applies assumptions to the baseline snapshot to produce simulated snapshot.
        Generates delta comparison.
        """
        baseline = dict(scenario.baseline_snapshot)
        simulated = dict(scenario.baseline_snapshot)
        
        assumptions = scenario.assumptions.all()
        
        # Deep copy elements that will be mutated in the simulated state
        simulated['skills'] = list(baseline.get('skills', []))
        
        for assumption in assumptions:
            data = assumption.structured_data
            
            if assumption.assumption_type == AssumptionType.SKILL:
                skill_name = data.get('skill')
                if skill_name:
                    simulated['skills'].append({
                        "name": skill_name,
                        "category": data.get('category', 'Simulated'),
                        "is_simulated": True
                    })
                    
            elif assumption.assumption_type == AssumptionType.INTERVIEW:
                improvement = data.get('improvement_points', 0)
                current = simulated.get('interview_readiness', 0)
                if isinstance(current, int):
                    simulated['interview_readiness'] = min(100, current + improvement)
                    
            elif assumption.assumption_type == AssumptionType.LOCATION:
                simulated['simulated_target_country'] = data.get('country', '')
                
        scenario.simulated_snapshot = simulated
        scenario.status = ScenarioStatus.SIMULATED
        scenario.save()
        
        return ScenarioSimulationEngine.calculate_delta(scenario)
        
    @staticmethod
    def calculate_delta(scenario):
        """Calculates differences between baseline and simulated snapshots."""
        baseline = scenario.baseline_snapshot
        simulated = scenario.simulated_snapshot
        
        # Example calculation
        baseline_skills = set([s['name'] for s in baseline.get('skills', [])])
        simulated_skills = set([s['name'] for s in simulated.get('skills', [])])
        
        acquired_skills = list(simulated_skills - baseline_skills)
        
        b_ir = baseline.get('interview_readiness')
        s_ir = simulated.get('interview_readiness')
        
        ir_delta = 0
        if isinstance(b_ir, int) and isinstance(s_ir, int):
            ir_delta = s_ir - b_ir
            
        return {
            "acquired_skills": acquired_skills,
            "interview_readiness_delta": ir_delta
        }


class PathwayRoadmapService:
    """
    Generates a staged learning and evidence roadmap for a simulated career path.
    Integrates with existing LearningRoadmap data structures conceptually.
    """
    @staticmethod
    def generate_stages(simulated_snapshot, target_path):
        """
        Produce structured stages (Foundation, Core, Evidence, Interview, Brand, Application)
        """
        if not target_path:
            return {}
            
        simulated_skills = [s['name'] for s in simulated_snapshot.get('skills', [])]
        reqs = target_path.requirements.all()
        
        missing_skills = [r.canonical_skill for r in reqs if r.canonical_skill not in simulated_skills]
        
        # Simulated stages
        stages = {
            "Stage 1 - Foundation": [],
            "Stage 2 - Core Competency": missing_skills,
            "Stage 3 - Evidence": ["Build Portfolio Projects"],
            "Stage 4 - Interview Readiness": ["Technical Mocks", "Behavioral Mocks"],
            "Stage 5 - Career Brand": ["Optimize LinkedIn", "Update Resume Headline"],
            "Stage 6 - Application Readiness": ["Match Target Role"]
        }
        
        return stages

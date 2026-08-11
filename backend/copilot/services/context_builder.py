import json
from profiles.services.candidate_context import CandidateContextService
from analytics.services.kpi_service import get_overview_kpis
from analytics.services.funnel_service import get_funnel_analytics

from learning.models import SkillGapAnalysis, LearningRoadmap, ProjectRecommendation

class CopilotContextBuilder:
    def __init__(self, user):
        self.user = user

    def build_context(self, thread, intent):
        """
        Builds the context payload ensuring ONLY verified candidate facts
        and authorized records are included.
        """
        context = {
            "verified_candidate_facts": self._get_verified_profile(),
        }

        if thread.job:
            context["job_context"] = self._get_job_context(thread.job)
        
        if thread.application:
            context["application_context"] = self._get_application_context(thread.application)
            
        if thread.resume_version:
            context["resume_context"] = self._get_resume_context(thread.resume_version)

        # Include analytics if intent requires it
        if intent in ['ANALYTICS', 'GENERAL_CAREER']:
            context["analytics_context"] = self._get_analytics_context()
            
        if intent in ['GROWTH', 'LEARNING', 'GENERAL_CAREER']:
            context["learning_context"] = self._get_learning_context()
            
        if intent in ['GROWTH', 'LEARNING', 'GENERAL_CAREER', 'RESUME_TAILOR']:
            context["evidence_context"] = self._get_evidence_context()

        if intent in ['GROWTH', 'LEARNING', 'GENERAL_CAREER', 'RESUME_TAILOR', 'PROFILE_OPTIMIZATION']:
            context["career_brand_context"] = self._get_career_brand_context()

        if intent in ['INTERVIEW_PREP', 'GENERAL_CAREER']:
            context["interview_context"] = self._get_interview_context()

        if intent in ['GROWTH', 'LEARNING', 'GENERAL_CAREER', 'CAREER_PATHWAY']:
            context["career_pathway_context"] = self._get_career_pathway_context()
            
        if intent in ['GROWTH', 'LEARNING', 'GENERAL_CAREER', 'CAREER_DECISION']:
            context["career_decisions"] = self._get_career_decision_context(self.user)
            context["career_execution"] = self._get_career_execution_context(self.user)
            context["career_operating_state"] = self._get_career_operating_state_context(self.user)
            context["career_outcomes"] = self._get_career_outcomes_context(self.user)

        return context

    def _get_verified_profile(self):
        return CandidateContextService.get_for_user(self.user)

    def _get_job_context(self, job):
            
        data = {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "country": getattr(job, 'country', 'UNKNOWN'),
            "employment_type": job.employment_type,
            "work_mode": job.work_mode,
            "is_sponsorship_offered": getattr(job, 'is_sponsorship_offered', 'UNKNOWN')
        }
        
        if job.requirements:
            data["requirements"] = job.requirements
            
        match = job.matches.filter(user=self.user).first()
        if match:
            data["match_score"] = match.overall_score
            data["skill_score"] = match.skill_score
            data["missing_skills"] = match.missing_skills
            
        return data

    def _get_application_context(self, app):
        if app.user != self.user:
            return {}
        return {
            "status": app.status,
            "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            "provider": getattr(app, 'provider', 'UNKNOWN')
        }

    def _get_resume_context(self, resume_version):
        if resume_version.resume.user != self.user:
            return {}
        return {
            "name": resume_version.resume.name,
            "version": resume_version.version_number,
            "is_locked": resume_version.is_locked,
            "ats_score": resume_version.resume.ats_score
        }

    def _get_analytics_context(self):
        try:
            kpi = get_overview_kpis(self.user, {})
            funnel = get_funnel_analytics(self.user, {})
            return {
                "kpis": kpi,
                "funnel": funnel
            }
        except Exception:
            return {}

    def _get_learning_context(self):
        try:
            context = {}
            # Latest Gap Analysis
            analysis = SkillGapAnalysis.objects.filter(user=self.user).order_by('-created_at').first()
            if analysis:
                context["active_target"] = analysis.target_type
                # Top 5 critical/high gaps
                gaps = analysis.gap_items.exclude(gap_type='NO_GAP').order_by('-priority_score')[:5]
                context["top_skill_gaps"] = [
                    {"skill": g.canonical_skill, "priority": g.priority_band, "reason": g.reason}
                    for g in gaps
                ]
            
            # Active Roadmap
            roadmap = LearningRoadmap.objects.filter(user=self.user, is_stale=False).order_by('-created_at').first()
            if roadmap:
                items = roadmap.items.exclude(status='COMPLETED').order_by('sequence')[:3]
                context["active_roadmap"] = [
                    {"skill": i.canonical_skill, "objective": i.objective, "effort": i.estimated_effort_hours}
                    for i in items
                ]
                
            # Projects
            projects = ProjectRecommendation.objects.filter(user=self.user, status='RECOMMENDED').order_by('-priority')[:2]
            if projects:
                context["recommended_projects"] = [
                    {"title": p.title, "target_skills": p.target_skills, "effort": p.estimated_effort_hours}
                    for p in projects
                ]
                
            return context
        except Exception:
            return {}

    def _get_evidence_context(self):
        try:
            # We delay import to avoid circular dependencies if any
            from evidence.services.github_service import CandidateEvidenceAggregationService
            summary = CandidateEvidenceAggregationService.get_user_evidence_summary(self.user)
            # Format nicely for Copilot so it doesn't get flooded with full raw DB details
            formatted_summary = []
            for skill, data in summary.items():
                formatted_summary.append({
                    "skill": skill,
                    "evidence_count": data.get("evidence_count"),
                    "sources": data.get("sources"),
                    "status": "EVIDENCE DETECTED (UNVERIFIED)"
                })
            
            return {
                "skill_evidence_summary": formatted_summary,
                "disclaimer": "EXTERNAL DATA IS NOT AUTOMATICALLY VERIFIED CANDIDATE TRUTH. Treat as unverified evidence."
            }
        except Exception:
            return {}

    def _get_career_brand_context(self):
        try:
            from career_brand.models import ProfessionalProfileAnalysis
            analysis = ProfessionalProfileAnalysis.objects.filter(user=self.user).order_by('-created_at').first()
            if not analysis:
                return {}
            
            recs = analysis.recommendations.filter(status='PENDING').order_by('-severity')[:5]
            
            return {
                "recruiter_readiness_score": analysis.recruiter_readiness_score,
                "completeness_score": analysis.completeness_score,
                "top_recommendations": [
                    {"section": r.section_type, "type": r.recommendation_type, "severity": r.severity, "explanation": r.explanation}
                    for r in recs
                ],
                "disclaimer": "Do NOT modify candidate verified facts based on professional profile claims. Claims must be treated as unverified."
            }
        except Exception:
            return {}

    def _get_interview_context(self):
        try:
            from interviews.models import MockInterviewSession, InterviewWeakness
            from interviews.services.AnalyticsServices import InterviewReadinessService
            
            readiness = InterviewReadinessService.calculate_readiness(self.user)
            
            recent_session = MockInterviewSession.objects.filter(
                user=self.user, status='COMPLETED'
            ).order_by('-completed_at').first()
            
            weaknesses = InterviewWeakness.objects.filter(
                user=self.user, severity__in=['HIGH', 'CRITICAL']
            ).order_by('-created_at')[:3]
            
            return {
                "overall_readiness": readiness,
                "recent_session_score": recent_session.overall_readiness_score if recent_session else None,
                "top_weaknesses": [
                    {"skill": w.skill, "severity": w.severity, "reason": w.reason_code}
                    for w in weaknesses
                ]
            }
        except Exception:
            return {}

    def _get_career_pathway_context(self):
        try:
            from career_pathways.models import CareerPathScenario
            latest_scenario = CareerPathScenario.objects.filter(
                user=self.user, status='SIMULATED'
            ).order_by('-created_at').first()
            
            if not latest_scenario:
                return {}
                
            return {
                "latest_scenario": {
                    "name": latest_scenario.name,
                    "target_path": latest_scenario.target_path.canonical_role_name if latest_scenario.target_path else latest_scenario.target_role,
                    "status": latest_scenario.status
                },
                "disclaimer": "SCENARIO_DATA_IS_HYPOTHETICAL. Do not treat scenario assumptions or simulated results as verified candidate facts."
            }
        except Exception:
            return {}

    def _get_career_decision_context(self, user) -> dict:
        """
        Retrieves the latest Phase 7G career decision plan for Copilot.
        """
        try:
            from career_decisions.models import CareerDecisionPlanVersion
            latest_plan = CareerDecisionPlanVersion.objects.filter(user=user, is_active=True).first()
            if not latest_plan:
                return {"status": "NO_ACTIVE_PLAN"}
                
            return {
                "disclaimer": "CAREER_DECISION_DATA_IS_ADVISORY. You are NOT permitted to modify CandidateContext, verification status, or application policy based on this data. You may only advise the candidate.",
                "generated_at": latest_plan.generated_at.isoformat(),
                "priorities": [
                    {
                        "category": p.category,
                        "severity": p.severity,
                        "explanation": p.explanation,
                        "recommended_action": p.recommended_action
                    }
                    for p in latest_plan.priorities.all()[:3]
                ],
                "next_actions": [
                    {
                        "title": a.title,
                        "action_type": a.action_type,
                        "status": a.status,
                        "reason": a.reason
                    }
                    for a in latest_plan.actions.filter(status='PENDING').order_by('-final_score')[:5]
                ]
            }
        except Exception:
            return {"status": "ERROR"}

    def _get_career_execution_context(self, user) -> dict:
        """
        Retrieves the latest Phase 7H career execution plan for Copilot.
        """
        try:
            from career_execution.models import CareerExecutionPlan, CareerExecutionProgress, ExecutionStatus
            plan = CareerExecutionPlan.objects.filter(user=user).first()
            if not plan:
                return {"status": "NO_ACTIVE_EXECUTION_PLAN"}
                
            progress = CareerExecutionProgress.objects.filter(user=user).order_by('-timestamp').first()
            
            return {
                "disclaimer": "CAREER_EXECUTION_DATA_IS_ADVISORY. Copilot may explain execution state but cannot modify execution authorization, verified facts, application policy, or action completion.",
                "progress": {
                    "overall_score": progress.overall_score if progress else 0,
                    "skill_score": progress.skill_score if progress else 0
                },
                "next_actions": [
                    {
                        "title": i.title,
                        "status": i.status,
                        "execution_mode": i.execution_mode
                    }
                    for i in plan.items.exclude(status__in=[ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED, ExecutionStatus.SUPERSEDED]).order_by('-final_score')[:5]
                ],
                "blocked_actions": [
                    {
                        "title": i.title,
                        "status": i.status,
                        "execution_mode": i.execution_mode
                    }
                    for i in plan.items.filter(status=ExecutionStatus.BLOCKED)[:3]
                ]
            }
        except Exception:
            return {"status": "ERROR"}

    def _get_career_operating_state_context(self, user) -> dict:
        """
        Retrieves the latest Phase 7I career operating state for Copilot.
        """
        try:
            from career_integration.models import CareerOperatingState
            state = CareerOperatingState.objects.filter(user=user).first()
            if not state:
                return {"status": "NO_OPERATING_STATE"}
                
            return {
                "disclaimer": "CAREER_OPERATING_STATE_IS_ADVISORY. DO NOT MODIFY VERIFIED CANDIDATE FACTS. DO NOT MODIFY VERIFICATION STATUS. DO NOT AUTHORIZE APPLICATION EXECUTION. DO NOT MODIFY AUTOMATION POLICY. DO NOT COMPLETE EXECUTION ACTIONS. DO NOT CONVERT HYPOTHETICAL DATA INTO REAL DATA. DO NOT OVERRIDE DOMAIN AUTHORITIES.",
                "overall_health": state.overall_health,
                "overall_readiness_score": state.overall_readiness_score,
                "current_primary_goal": state.current_primary_goal,
                "top_blocker": state.top_blocker,
                "execution_velocity_score": state.execution_velocity_score,
                "application_momentum_score": state.application_momentum_score,
                "domains": [
                    {"domain_name": d.domain_name, "status": d.status}
                    for d in state.domains.all()
                ]
            }
        except Exception:
            return {"status": "ERROR"}

    def _get_career_outcomes_context(self, user) -> dict:
        """
        Exposes Phase 8 outcome intelligence to Copilot safely.
        """
        try:
            from career_outcomes.services.funnel_analysis_service import FunnelAnalysisService
            from career_outcomes.services.recommendation_engine import RecommendationEngineService
            
            return {
                "disclaimer": "CAREER_OUTCOME_DATA_IS_ADVISORY. Outcomes are historical observations. Correlations are not causation. Copilot cannot modify outcomes, verified facts, decisions, or execution states.",
                "funnel": FunnelAnalysisService.calculate_funnel(user),
                "recommendations": RecommendationEngineService.generate_recommendations(user)
            }
        except Exception:
            return {"status": "ERROR"}

from career_decisions.models import CareerAction, ActionType, ActionStatus, CareerActionDependency

class ActionRankingService:
    @staticmethod
    def calculate_score(impact, urgency, readiness, effort, deps_count):
        """
        Deterministic formula required by Phase 7G prompt:
        impact + urgency + readiness - effort_penalty - dependency_penalty
        Bounded to 0-100.
        """
        score = impact + urgency + readiness - (effort * 0.5) - (deps_count * 10)
        return max(0, min(100, int(score)))

class ActionDependencyEngine:
    """
    Manages generation and linking of concrete actions.
    """
    
    @staticmethod
    def generate_actions_for_plan(plan_version, priorities):
        actions = []
        
        # We simulate a concrete graph generation
        has_skill_gap = any(p['category'] == 'SKILL_GAP' for p in priorities)
        has_brand_gap = any(p['category'] == 'CAREER_BRAND_GAP' for p in priorities)
        has_interview_gap = any(p['category'] == 'INTERVIEW_GAP' for p in priorities)
        
        if has_skill_gap:
            a1 = CareerAction.objects.create(
                plan_version=plan_version,
                title="Acquire Missing Target Skills",
                description="Complete roadmap courses for missing skills.",
                action_type=ActionType.USER_ACTION_REQUIRED,
                impact_score=80,
                urgency_score=50,
                effort_penalty=60,
                reason="SKILL_GAP identified"
            )
            a1.final_score = ActionRankingService.calculate_score(a1.impact_score, a1.urgency_score, 20, a1.effort_penalty, 0)
            a1.save()
            actions.append(a1)
            
        if has_brand_gap:
            a2 = CareerAction.objects.create(
                plan_version=plan_version,
                title="Optimize LinkedIn Profile",
                description="Update career brand according to optimization suggestions.",
                action_type=ActionType.PREPARE,
                impact_score=60,
                urgency_score=70,
                effort_penalty=20,
                reason="CAREER_BRAND_GAP identified"
            )
            a2.final_score = ActionRankingService.calculate_score(a2.impact_score, a2.urgency_score, 80, a2.effort_penalty, 0)
            a2.save()
            actions.append(a2)
            
        if has_interview_gap:
            a3 = CareerAction.objects.create(
                plan_version=plan_version,
                title="Mock Interview Practice",
                description="Complete 3 STAR behavioral mocks.",
                action_type=ActionType.USER_ACTION_REQUIRED,
                impact_score=70,
                urgency_score=80,
                effort_penalty=30,
                reason="INTERVIEW_GAP identified"
            )
            a3.final_score = ActionRankingService.calculate_score(a3.impact_score, a3.urgency_score, 50, a3.effort_penalty, 1 if has_skill_gap else 0)
            a3.save()
            actions.append(a3)
            
            # Example dependency setup (Interview prep depends on having skills first)
            if has_skill_gap:
                CareerActionDependency.objects.create(action=a3, depends_on=actions[0])
                
        # Auto-Apply Action (Phase 5F Integration)
        apply_action = CareerAction.objects.create(
            plan_version=plan_version,
            title="Auto-Apply to High-Match Roles",
            description="Execute automated applications for target paths.",
            action_type=ActionType.USER_ACTION_REQUIRED, # Default to safe state
            impact_score=100,
            urgency_score=90,
            effort_penalty=0,
            reason="Continuous Application Strategy"
        )
        # Apply requires everything else to be resolved first
        deps = 0
        if has_skill_gap:
            CareerActionDependency.objects.create(action=apply_action, depends_on=actions[0])
            deps += 1
        if has_brand_gap:
            CareerActionDependency.objects.create(action=apply_action, depends_on=actions[1])
            deps += 1
            
        apply_action.final_score = ActionRankingService.calculate_score(apply_action.impact_score, apply_action.urgency_score, 100, apply_action.effort_penalty, deps)
        
        # Phase 5F Integration check
        from career_decisions.services.autoapply_service import AutoApplyEligibilityService
        
        if AutoApplyEligibilityService.is_eligible_for_automation(apply_action, plan_version.user):
            apply_action.action_type = ActionType.AUTO_EXECUTABLE
            apply_action.reason = "Continuous Application Strategy (Automation Eligible)"
        else:
            apply_action.action_type = ActionType.USER_ACTION_REQUIRED
            apply_action.reason = "Review required or limits reached"
            
        apply_action.save()
        actions.append(apply_action)
        
        return actions

class ActionCompletionService:
    """
    Checks database for completion of action conditions without LLMs.
    """
    @staticmethod
    def check_completion(action):
        # We would inspect real database models here based on action reason/title
        if "Skill" in action.title:
            pass # check CandidateContext
        return False

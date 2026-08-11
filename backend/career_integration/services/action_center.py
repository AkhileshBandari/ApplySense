import logging
from career_integration.models import UserActionItem, SystemBlocker, DomainName
from profiles.models import Profile
from evidence.models import GitHubConnection
from automation.models import AutoApplyRun

logger = logging.getLogger(__name__)

class ActionCenterService:
    """Evaluates blockers and generates UserActionItems."""
    
    @classmethod
    def recalculate_actions(cls, user):
        """Scans domain state and creates or resolves UserActionItems."""
        logger.info(f"Recalculating OS actions for user {user.id}")
        
        # 1. Missing Context
        has_context = Profile.objects.filter(user=user).exists()
        cls._upsert_action(
            user=user,
            domain=DomainName.CONTEXT,
            blocker=SystemBlocker.MISSING_VERIFIED_SKILL,
            title="Complete your verified candidate profile",
            description="We need your verified skills to start mapping your career OS.",
            priority=100,
            is_active=not has_context
        )
        
        # 2. Missing Evidence (GitHub)
        has_github = GitHubConnection.objects.filter(user=user).exists()
        cls._upsert_action(
            user=user,
            domain=DomainName.EVIDENCE,
            blocker=SystemBlocker.MISSING_EVIDENCE,
            title="Connect your GitHub account",
            description="Provide verified evidence to empower your career brand.",
            priority=80,
            is_active=not has_github
        )
        
        # 3. Action Required from Automation
        action_required_runs = AutoApplyRun.objects.filter(user=user, applications_user_action_required__gt=0)
        active_run_ids = set()
        
        for run in action_required_runs:
            active_run_ids.add(run.id)
            cls._upsert_action(
                user=user,
                domain=DomainName.EXECUTION,
                blocker=SystemBlocker.USER_ACTION_REQUIRED,
                title=f"Action Required for Auto-Apply #{run.id}",
                description="Your auto-apply run requires intervention (e.g. CAPTCHA, Consent).",
                priority=90,
                is_active=True,
                context_data={"run_id": run.id}
            )
            
        # Resolve any that are no longer active
        existing_automation_actions = UserActionItem.objects.filter(
            user=user, 
            blocker_type=SystemBlocker.USER_ACTION_REQUIRED,
            is_resolved=False
        )
        for action in existing_automation_actions:
            run_id = action.context_data.get("run_id")
            if run_id not in active_run_ids:
                action.is_resolved = True
                action.save()

    @classmethod
    def _upsert_action(cls, user, domain, blocker, title, description, priority, is_active, context_data=None):
        context_data = context_data or {}
        
        if is_active:
            action, created = UserActionItem.objects.get_or_create(
                user=user,
                source_domain=domain,
                blocker_type=blocker,
                context_data=context_data,
                defaults={
                    'title': title,
                    'description': description,
                    'priority': priority
                }
            )
            if not created and action.is_resolved:
                action.is_resolved = False
                action.save()
        else:
            UserActionItem.objects.filter(
                user=user,
                source_domain=domain,
                blocker_type=blocker,
                context_data=context_data,
                is_resolved=False
            ).update(is_resolved=True)

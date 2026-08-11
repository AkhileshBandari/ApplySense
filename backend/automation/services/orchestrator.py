import logging
from django.utils import timezone
from automation.models import AutoApplyRun, AutoApplyRunItem
from applications.models import Application, ApplicationExecution
from applications.services.execution_domain import (
    ExecutionReservationService, ServerExecutionCapabilityResolver
)
from jobs.registries import ApplicationProviderRegistry

logger = logging.getLogger(__name__)

class AutoApplyOrchestrator:
    def __init__(self, run: AutoApplyRun):
        self.run = run
        self.user = run.user
        
    def execute(self):
        self.run.status = 'RUNNING'
        self.run.started_at = timezone.now()
        self.run.save()
        
        try:
            # 1. DISCOVER: Get candidate jobs (Mocked for testing limits)
            # In real system: pull from scraper or matching engine.
            jobs_to_evaluate = self._discover_jobs()
            self.run.jobs_discovered = len(jobs_to_evaluate)
            
            for job in jobs_to_evaluate:
                self.run.jobs_evaluated += 1
                
                # 2. MATCH & POLICY CHECK
                if not self._evaluate_policy(job):
                    continue
                    
                self.run.jobs_matched += 1
                
                # 3. CREATE APPLICATION & PREPARE
                application = self._prepare_application(job)
                if not application:
                    continue
                    
                # 4. EXECUTION ROUTING
                self._execute_application(application)
                
            self.run.status = 'COMPLETED'
        except Exception as e:
            logger.error(f"AutoApplyRun {self.run.id} failed: {str(e)}")
            self.run.status = 'FAILED'
            self.run.metadata['error'] = str(e)
        finally:
            self.run.finished_at = timezone.now()
            self.run.save()

    def _discover_jobs(self):
        from jobs.models import JobMatch
        from applications.models import Application
        
        try:
            from automation.models import AutomationPolicy
            policy = AutomationPolicy.objects.get(user=self.user)
            min_score = policy.minimum_match_score
        except Exception:
            min_score = 75
            
        applied_job_ids = Application.objects.filter(user=self.user).values_list('job_id', flat=True)
        matches = JobMatch.objects.filter(
            user=self.user,
            overall_score__gte=min_score
        ).exclude(job_id__in=applied_job_ids).order_by('-overall_score')[:50]
        
        return [match.job for match in matches]
        
    def _evaluate_policy(self, job):
        from automation.models import AutomationPolicy
        from applications.models import Application
        
        try:
            policy = AutomationPolicy.objects.get(user=self.user)
        except Exception:
            return False
            
        if not policy.automation_enabled or policy.global_pause:
            return False
            
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_count = Application.objects.filter(
            user=self.user,
            created_at__gte=today,
            source='AUTO_APPLY'
        ).count()
        
        if daily_count >= policy.daily_application_limit:
            return False
            
        week_ago = timezone.now() - timezone.timedelta(days=7)
        weekly_count = Application.objects.filter(
            user=self.user,
            created_at__gte=week_ago,
            source='AUTO_APPLY'
        ).count()
        
        if weekly_count >= policy.weekly_application_limit:
            return False
            
        if not job.url:
            return False
            
        return True
        
    def _prepare_application(self, job):
        from applications.models import Application
        
        provider = 'generic'
        if job.url:
            url_lower = job.url.lower()
            if 'lever.co' in url_lower: provider = 'lever'
            elif 'greenhouse.io' in url_lower: provider = 'greenhouse'
            elif 'ashbyhq.com' in url_lower: provider = 'ashby'
            
        application, created = Application.objects.get_or_create(
            user=self.user,
            job=job,
            defaults={
                'status': 'PREPARED',
                'source': 'AUTO_APPLY',
                'application_provider': provider,
                'company': getattr(job, 'company', ''),
                'role': getattr(job, 'title', '')
            }
        )
        if not created:
            return None
            
        return application
        
    def _execute_application(self, application):
        provider = application.application_provider
        capability = ApplicationProviderRegistry.get_capability(provider)
        
        mode, reason = ServerExecutionCapabilityResolver.resolve(
            application=application,
            provider=provider,
            source=application.source,
            provider_capability=capability,
            policy=self.user.automation_policy,
            authorization_state='UNVERIFIED'
        )
        
        if mode == 'USER_ACTION_REQUIRED':
            from automation.models import UserActionRequired
            UserActionRequired.objects.create(
                user=self.user,
                application=application,
                reason=reason
            )
            self.run.applications_user_action_required += 1
            return
            
        if mode == 'BLOCKED':
            self.run.applications_blocked += 1
            return
            
        if mode == 'SERVER_BROWSER':
            # Reserve slot atomically
            success, execution, error = ExecutionReservationService.reserve_execution_slot(
                user=self.user,
                application=application,
                idempotency_key=f"auto_apply_{self.run.id}_{application.id}"
            )
            if not success:
                self.run.applications_blocked += 1
                return
                
            # Execute
            from automation.services.server_browser import ServerBrowserExecutionService
            service = ServerBrowserExecutionService()
            result = service.execute(execution)
            
            if result:
                self.run.applications_submitted += 1
            else:
                self.run.applications_failed += 1

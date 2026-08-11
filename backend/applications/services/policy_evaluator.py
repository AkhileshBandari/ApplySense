import json
import re
from django.utils import timezone
from datetime import timedelta
from applications.models import Application, AutomationPolicy, AutomationRule, PolicyDecision

class AutomationPolicyEvaluator:
    """
    Evaluates whether an application meets the user's AutomationPolicy rules to proceed.
    """
    @staticmethod
    def evaluate(application: Application) -> PolicyDecision:
        user = application.user
        
        try:
            policy = user.automation_policy
        except AutomationPolicy.DoesNotExist:
            # Default restrictive policy
            policy = AutomationPolicy.objects.create(user=user)
            
        if policy.global_pause:
            return AutomationPolicyEvaluator._record_decision(
                application, 'BLOCK', ['GLOBAL_PAUSE_ACTIVE']
            )
            
        if not policy.automation_enabled:
            return AutomationPolicyEvaluator._record_decision(
                application, 'REQUIRE_REVIEW', ['AUTOMATION_DISABLED']
            )

        reasons = []
        
        # Check Limits
        now = timezone.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        
        daily_count = Application.objects.filter(
            user=user, 
            submitted_at__gte=day_ago
        ).count()
        
        weekly_count = Application.objects.filter(
            user=user, 
            submitted_at__gte=week_ago
        ).count()
        
        if daily_count >= policy.daily_application_limit:
            reasons.append('DAILY_LIMIT_EXCEEDED')
            
        if weekly_count >= policy.weekly_application_limit:
            reasons.append('WEEKLY_LIMIT_EXCEEDED')
            
        # Match Score
        if application.match_score < policy.minimum_match_score:
            reasons.append('MATCH_SCORE_TOO_LOW')
            
        # Rules Evaluation
        for rule in policy.rules.all():
            if rule.rule_type == 'EXCLUDED_COMPANY':
                company = (application.company or '').lower()
                excluded = [c.lower() for c in rule.value.get('companies', [])]
                if any(c in company for c in excluded):
                    reasons.append('EXCLUDED_COMPANY_MATCHED')
                    
            elif rule.rule_type == 'MINIMUM_COMPENSATION':
                # Simplified rule - would require currency matching in prod
                if application.job and application.job.salary_max:
                    min_req = rule.value.get('minimum_amount', 0)
                    if application.job.salary_max < min_req:
                        reasons.append('COMPENSATION_TOO_LOW')
                        
        if reasons:
            return AutomationPolicyEvaluator._record_decision(
                application, 'BLOCK', reasons
            )
            
        if policy.require_review_before_submit:
            return AutomationPolicyEvaluator._record_decision(
                application, 'REQUIRE_REVIEW', ['REVIEW_REQUIRED_BY_POLICY']
            )
            
        return AutomationPolicyEvaluator._record_decision(
            application, 'ALLOW_PREPARATION', []
        )
        
    @staticmethod
    def _record_decision(application: Application, decision: str, reasons: list) -> PolicyDecision:
        return PolicyDecision.objects.create(
            application=application,
            decision=decision,
            reason_codes=reasons
        )

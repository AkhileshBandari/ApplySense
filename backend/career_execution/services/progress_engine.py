from career_execution.models import CareerExecutionProgress, CareerExecutionItem, ExecutionStatus

class CareerProgressEngine:
    @staticmethod
    def calculate_progress(user):
        """
        Calculates bounded 0-100 deterministic progress metrics without using LLMs.
        """
        from career_execution.models import CareerExecutionPlan
        plan = CareerExecutionPlan.objects.filter(user=user).first()
        
        if not plan:
            return CareerExecutionProgress.objects.create(user=user)
            
        items = list(plan.items.all())
        if not items:
            return CareerExecutionProgress.objects.create(user=user)
            
        def safe_percent(completed, total):
            if total == 0:
                return 0
            return max(0, min(100, int((completed / total) * 100)))

        # Counters
        metrics = {
            'overall_total': 0, 'overall_completed': 0,
            'skill_total': 0, 'skill_completed': 0,
            'evidence_total': 0, 'evidence_completed': 0,
            'brand_total': 0, 'brand_completed': 0,
            'interview_total': 0, 'interview_completed': 0,
            'application_total': 0, 'application_completed': 0,
        }
        
        for item in items:
            if item.status in [ExecutionStatus.SUPERSEDED, ExecutionStatus.CANCELLED]:
                continue
                
            is_completed = 1 if item.status == ExecutionStatus.COMPLETED else 0
            metrics['overall_total'] += 1
            metrics['overall_completed'] += is_completed
            
            # Map based on reason/source_phase
            phase = item.source_phase or ""
            reason = item.reason or ""
            
            if 'LEARNING' in phase or 'SKILL' in reason:
                metrics['skill_total'] += 1
                metrics['skill_completed'] += is_completed
            elif 'EVIDENCE' in phase or 'EVIDENCE' in reason:
                metrics['evidence_total'] += 1
                metrics['evidence_completed'] += is_completed
            elif 'BRAND' in phase or 'BRAND' in reason:
                metrics['brand_total'] += 1
                metrics['brand_completed'] += is_completed
            elif 'INTERVIEW' in phase or 'INTERVIEW' in reason:
                metrics['interview_total'] += 1
                metrics['interview_completed'] += is_completed
            elif 'APPLICATION' in phase or 'APPLY' in reason or 'AUTO' in reason:
                metrics['application_total'] += 1
                metrics['application_completed'] += is_completed
                
        progress = CareerExecutionProgress.objects.create(
            user=user,
            overall_score=safe_percent(metrics['overall_completed'], metrics['overall_total']),
            skill_score=safe_percent(metrics['skill_completed'], metrics['skill_total']),
            evidence_score=safe_percent(metrics['evidence_completed'], metrics['evidence_total']),
            brand_score=safe_percent(metrics['brand_completed'], metrics['brand_total']),
            interview_score=safe_percent(metrics['interview_completed'], metrics['interview_total']),
            application_score=safe_percent(metrics['application_completed'], metrics['application_total']),
            pathway_score=0 # Determined elsewhere if needed
        )
        return progress

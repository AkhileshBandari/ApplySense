from django.utils import timezone
from applications.models import Application, ApplicationStatusHistory

class ApplicationStateMachine:
    
    VALID_TRANSITIONS = {
        'DRAFT': ['PREPARING', 'WITHDRAWN'],
        'PREPARING': ['REVIEW_REQUIRED', 'READY_TO_SUBMIT', 'WITHDRAWN'],
        'REVIEW_REQUIRED': ['READY_TO_SUBMIT', 'PREPARING', 'WITHDRAWN'],
        'READY_TO_SUBMIT': ['SUBMITTING', 'REVIEW_REQUIRED', 'WITHDRAWN'],
        'SUBMITTING': ['SUBMITTED', 'APPLICATION_FAILED'],
        'SUBMITTED': ['UNDER_REVIEW', 'ASSESSMENT', 'INTERVIEW', 'REJECTED', 'WITHDRAWN'],
        'UNDER_REVIEW': ['ASSESSMENT', 'INTERVIEW', 'REJECTED', 'WITHDRAWN'],
        'ASSESSMENT': ['INTERVIEW', 'REJECTED', 'WITHDRAWN'],
        'INTERVIEW': ['FINAL_ROUND', 'OFFER', 'REJECTED', 'WITHDRAWN'],
        'FINAL_ROUND': ['OFFER', 'REJECTED', 'WITHDRAWN'],
        'OFFER': ['ACCEPTED', 'DECLINED', 'WITHDRAWN'],
        'APPLICATION_FAILED': ['PREPARING', 'DRAFT', 'WITHDRAWN'],
    }

    @staticmethod
    def transition(application: Application, new_status: str, source: str, reason: str = "") -> bool:
        current = application.status
        
        # If it's already in the status, do nothing
        if current == new_status:
            return True
            
        allowed = ApplicationStateMachine.VALID_TRANSITIONS.get(current, [])
        
        # Manual bypass for admins or specific overrides if needed could be added here
        
        if new_status not in allowed:
            raise ValueError(f"Invalid state transition from {current} to {new_status}")
            
        # Write history
        ApplicationStatusHistory.objects.create(
            application=application,
            previous_status=current,
            new_status=new_status,
            source=source,
            reason=reason
        )
        
        from applications.models import ApplicationAuditLog
        ApplicationAuditLog.objects.create(
            application=application,
            event_type='STATUS_CHANGED',
            actor=source,
            metadata={'previous': current, 'new': new_status, 'reason': reason}
        )
        
        # Update Application
        application.status = new_status
        application.last_status_change_at = timezone.now()
        
        if new_status == 'PREPARING':
            application.preparation_status = 'IN_PROGRESS'
        elif new_status == 'SUBMITTING':
            application.submission_status = 'IN_PROGRESS'
        elif new_status == 'SUBMITTED':
            application.submission_status = 'COMPLETED'
            application.submitted_at = timezone.now()
            
        application.save()
        return True

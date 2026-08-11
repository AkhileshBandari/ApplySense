from applications.models import Application

class ApplicationDuplicateService:
    @staticmethod
    def check_duplicate(user, job_id: int = None, external_identifier: str = None) -> str:
        """
        Returns: NO_DUPLICATE, POSSIBLE_DUPLICATE, PREVIOUSLY_APPLIED
        Different users are independent.
        """
        if not job_id and not external_identifier:
            return 'NO_DUPLICATE'

        qs = Application.objects.filter(user=user).exclude(status__in=['DRAFT', 'PREPARING', 'WITHDRAWN'])
        
        if job_id:
            qs = qs.filter(job_id=job_id)
        elif external_identifier:
            qs = qs.filter(external_identifier=external_identifier)
            
        if not qs.exists():
            return 'NO_DUPLICATE'
            
        # If it exists, check status
        has_active_submission = qs.filter(status__in=['SUBMITTING', 'SUBMITTED', 'UNDER_REVIEW', 'ASSESSMENT', 'INTERVIEW', 'FINAL_ROUND', 'OFFER']).exists()
        if has_active_submission:
            return 'PREVIOUSLY_APPLIED'
            
        has_failed = qs.filter(status__in=['APPLICATION_FAILED', 'REJECTED']).exists()
        if has_failed:
            return 'POSSIBLE_DUPLICATE'
            
        return 'PREVIOUSLY_APPLIED'

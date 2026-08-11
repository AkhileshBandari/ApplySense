import json
from django.utils import timezone
from applications.models import Application, ApplicationQuestion
from resumes.models import ResumeVersion
from profiles.services.candidate_context import CandidateContextService
from applications.services.answer_resolver import ApplicationAnswerResolver
from applications.services.state_machine import ApplicationStateMachine
from applications.services.duplicate_service import ApplicationDuplicateService

class ApplicationPreparationService:
    """
    Evaluates an application for readiness, creates the immutable snapshot,
    and resolves application questions.
    """

    @staticmethod
    def _create_snapshot(application: Application, user, job, resume_version: ResumeVersion):
        """
        Builds the immutable snapshot for historical reproducibility.
        """
        context = CandidateContextService.get_for_user(user)
        snapshot = {
            "job": {
                "id": job.id if job else None,
                "title": job.title if job else application.role,
                "company": job.company if job else application.company,
                "url": job.url if job else application.application_url,
                "requirements": job.requirements if job else {},
            },
            "resume_version": {
                "id": resume_version.id if resume_version else None,
                "version_name": resume_version.version_name if resume_version else None,
                "structured_content": resume_version.structured_content if resume_version else {},
            },
            "candidate_context": context,
            "prepared_at": timezone.now().isoformat()
        }
        return snapshot

    @staticmethod
    def prepare_application(application: Application, user, resume_version: ResumeVersion = None):
        """
        Transitions application to PREPARING, validates, resolves questions, 
        evaluates readiness, and transitions to REVIEW_REQUIRED or READY_TO_SUBMIT.
        """
        ApplicationStateMachine.transition(application, 'PREPARING', source='SYSTEM')
        
        job = application.job
        
        # 1. Ensure Resume ownership
        if resume_version and resume_version.user != user:
            raise ValueError("Cannot use a ResumeVersion belonging to another user.")
            
        if resume_version:
            application.resume_version = resume_version
            
        # 2. Build Snapshot
        application.snapshot = ApplicationPreparationService._create_snapshot(
            application=application,
            user=user,
            job=job,
            resume_version=application.resume_version
        )
        
        # Lock Resume Version
        if application.resume_version:
            application.resume_version.is_locked = True
            application.resume_version.save()
            
        # 3. Resolve existing questions
        questions = application.questions.all()
        for q in questions:
            if q.review_status not in ['AUTO_RESOLVED', 'APPROVED']:
                resolution = ApplicationAnswerResolver.resolve(user, q.question_text, q.category)
                q.answer = resolution['answer']
                q.answer_source = resolution['source']
                q.review_status = resolution['review_status']
                q.save()
                
        # 4. Evaluate Readiness
        readiness = ApplicationPreparationService.evaluate_readiness(application)
        
        # 5. Determine next state based on readiness
        if readiness['status'] == 'READY':
            ApplicationStateMachine.transition(application, 'READY_TO_SUBMIT', source='SYSTEM')
        else:
            ApplicationStateMachine.transition(application, 'REVIEW_REQUIRED', source='SYSTEM')
            
        application.prepared_at = timezone.now()
        application.save()
        
        return readiness
        
    @staticmethod
    def evaluate_readiness(application: Application) -> dict:
        """
        Determines the deterministic readiness state.
        Returns hard blockers and warnings.
        """
        blockers = []
        warnings = []
        
        if not application.resume_version:
            blockers.append("A Resume Version must be selected.")
            
        if application.job and application.job.is_closed:
            blockers.append("This job is no longer accepting applications.")
            
        unanswered_required = []
        needs_review = []
        
        for q in application.questions.all():
            if q.required and not q.answer and q.review_status == 'USER_INPUT_REQUIRED':
                unanswered_required.append(q.question_key)
            elif q.review_status in ['USER_INPUT_REQUIRED', 'REVIEW_RECOMMENDED']:
                needs_review.append(q.question_key)
                
        if unanswered_required:
            blockers.append(f"Missing required answers for: {', '.join(unanswered_required)}")
            
        if needs_review:
            warnings.append(f"Answers need review for: {', '.join(needs_review)}")
            
        if application.match_score < 50:
            warnings.append("This is a stretch role. Ensure your tailored resume highlights relevant overlap.")
            
        status = 'READY'
        if blockers:
            status = 'NOT_READY'
        elif warnings:
            status = 'NEEDS_REVIEW'
            
        return {
            'status': status,
            'blockers': blockers,
            'warnings': warnings,
            'unanswered_required': unanswered_required,
            'needs_review': needs_review
        }

    @staticmethod
    def duplicate_check(user, job_id: int, external_identifier: str = None) -> bool:
        """
        Checks if the user has already applied to this exact job.
        """
        dup_status = ApplicationDuplicateService.check_duplicate(user, job_id, external_identifier)
        return dup_status in ['PREVIOUSLY_APPLIED', 'POSSIBLE_DUPLICATE']

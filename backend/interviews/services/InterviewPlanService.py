from interviews.models import InterviewPlan, InterviewPlanSection
from .InterviewRequirementAnalysisService import InterviewRequirementAnalysisService

class InterviewPlanService:
    @staticmethod
    def generate_plan(user, job=None, application=None, resume_version=None, target_role=None, interview_type='GENERAL', difficulty='INTERMEDIATE'):
        """
        Generates a structured InterviewPlan and InterviewPlanSections.
        """
        # Create the plan
        plan = InterviewPlan.objects.create(
            user=user,
            job=job,
            application=application,
            resume_version=resume_version,
            target_role=target_role,
            interview_type=interview_type,
            difficulty=difficulty,
            status='CREATED'
        )
        
        # Determine context snapshot
        snapshot = {
            'target_role': target_role,
            'interview_type': interview_type,
            'difficulty': difficulty
        }
        
        if job:
            snapshot['job_id'] = job.id
            snapshot['job_title'] = job.title
        
        if resume_version:
            snapshot['resume_version_id'] = resume_version.id
            
        plan.context_snapshot = snapshot
        plan.save()
        
        # Build sections based on interview_type
        sections = []
        
        if interview_type in ['GENERAL', 'JOB_SPECIFIC', 'TECHNICAL']:
            sections.append({
                'section_type': 'TECHNICAL',
                'priority': 1,
                'reason_code': 'JOB_REQUIRED',
                'estimated_weight': 0.4
            })
            
        if interview_type in ['GENERAL', 'JOB_SPECIFIC', 'BEHAVIORAL', 'HR']:
            sections.append({
                'section_type': 'BEHAVIORAL',
                'priority': 2,
                'reason_code': 'STANDARD_BEHAVIORAL',
                'estimated_weight': 0.3
            })
            
        if interview_type in ['RESUME_DEEP_DIVE', 'GENERAL'] and resume_version:
            sections.append({
                'section_type': 'RESUME',
                'priority': 3,
                'reason_code': 'RESUME_PROMINENCE',
                'estimated_weight': 0.2
            })
            
        if interview_type in ['SYSTEM_DESIGN', 'TECHNICAL']:
            sections.append({
                'section_type': 'SYSTEM_DESIGN',
                'priority': 4,
                'reason_code': 'SENIORITY_EXPECTATION',
                'estimated_weight': 0.1
            })
            
        for sec in sections:
            InterviewPlanSection.objects.create(
                plan=plan,
                section_type=sec['section_type'],
                priority=sec['priority'],
                reason_code=sec['reason_code'],
                estimated_weight=sec['estimated_weight']
            )
            
        return plan

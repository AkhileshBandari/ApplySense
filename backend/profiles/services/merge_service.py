from profiles.models import (
    Profile, Experience, Education, Skill, Project, 
    Certification, Achievement, Language, VerificationStatus
)

class MergeService:
    @staticmethod
    def accept_fact(user, model_class, fact_id):
        """Marks a fact as VERIFIED."""
        try:
            fact = model_class.objects.get(id=fact_id, profile=user.profile)
            fact.verification_status = VerificationStatus.VERIFIED
            fact.save()
            return True, fact
        except model_class.DoesNotExist:
            return False, None

    @staticmethod
    def reject_fact(user, model_class, fact_id):
        """Marks a fact as REJECTED."""
        try:
            fact = model_class.objects.get(id=fact_id, profile=user.profile)
            fact.verification_status = VerificationStatus.REJECTED
            fact.save()
            return True, fact
        except model_class.DoesNotExist:
            return False, None

    @staticmethod
    def edit_fact(user, model_class, fact_id, update_data):
        """Updates a fact and marks it VERIFIED."""
        try:
            fact = model_class.objects.get(id=fact_id, profile=user.profile)
            for key, value in update_data.items():
                if hasattr(fact, key) and key not in ['id', 'profile', 'source', 'source_resume']:
                    setattr(fact, key, value)
            fact.verification_status = VerificationStatus.VERIFIED
            fact.save()
            return True, fact
        except model_class.DoesNotExist:
            return False, None

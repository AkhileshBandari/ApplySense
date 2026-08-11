import logging
from typing import List, Dict, Any
from django.db import transaction
from applications.models import (
    Application, FormSession, DetectedApplicationForm, DetectedApplicationFormField, FormSessionAuditLog,
    ApplicationQuestion
)
from applications.services.answer_resolver import ApplicationAnswerResolver
from applications.services.policy_evaluator import AutomationPolicyEvaluator
from resumes.models import ResumeVersion

logger = logging.getLogger(__name__)

class FormIntelligenceService:
    """
    Handles Phase 5C intelligence: receiving raw fields from the extension, mapping them to canonical keys,
    resolving answers via Phase 5A rules, and enforcing safety boundaries.
    """
    
    @staticmethod
    @transaction.atomic
    def initialize_session(user, application_id: int, provider: str, url: str) -> FormSession:
        application = Application.objects.get(id=application_id, user=user)
        session = FormSession.objects.create(
            user=user,
            application=application,
            provider=provider,
            url=url,
            status='DETECTED'
        )
        FormSessionAuditLog.objects.create(session=session, action='SESSION_INITIALIZED')
        return session

    @staticmethod
    @transaction.atomic
    def process_form_schema(session: FormSession, fields_data: List[Dict[str, Any]], raw_schema: dict = None) -> DetectedApplicationForm:
        # Evaluate policy before analyzing fields
        policy_decision = AutomationPolicyEvaluator.evaluate(session.application)
        
        detected_form = DetectedApplicationForm.objects.create(
            session=session,
            raw_schema=raw_schema
        )
        
        for field_data in fields_data:
            normalized_key, category, confidence = FormIntelligenceService._classify_field(field_data)
            
            field_instance = DetectedApplicationFormField.objects.create(
                form=detected_form,
                provider_field_id=field_data.get('id', ''),
                label=field_data.get('label', ''),
                name_attribute=field_data.get('name', ''),
                input_type=field_data.get('type', 'text'),
                options=field_data.get('options', []),
                required=field_data.get('required', False),
                normalized_key=normalized_key,
                category=category,
                confidence=confidence,
                current_value=field_data.get('value', '')
            )
            
            # Record Audit
            FormSessionAuditLog.objects.create(
                session=session,
                action='FIELD_DETECTED',
                field_key=normalized_key,
                details={'label': field_instance.label}
            )
            
            # Resolve if not blocked by policy
            if policy_decision.decision != 'BLOCK':
                FormIntelligenceService._resolve_field(session, field_instance)
        
        session.status = 'ANALYZED'
        session.save()
        return detected_form

    @staticmethod
    def _classify_field(field_data: Dict[str, Any]) -> tuple:
        """
        Deterministic field classifier.
        Maps generic labels/names to canonical ApplySense keys.
        Returns: (normalized_key, category, confidence)
        """
        label = str(field_data.get('label', '')).lower()
        name = str(field_data.get('name', '')).lower()
        input_type = str(field_data.get('type', '')).lower()
        
        combined_text = f"{label} {name}"
        
        # Secret/Sensitive fields
        if any(term in combined_text for term in ['password', 'passcode', 'otp', 'verification code', 'captcha', 'access token', 'api key', 'security code']):
            return ('SECRET', 'SECRET', 1.0)
            
        # Exact/Strong Matches
        if 'first name' in label or name == 'firstname':
            return ('FIRST_NAME', 'PERSONAL', 1.0)
        elif 'last name' in label or name == 'lastname':
            return ('LAST_NAME', 'PERSONAL', 1.0)
        elif 'email' in combined_text and 'email' in input_type:
            return ('EMAIL', 'PERSONAL', 1.0)
        elif 'phone' in combined_text and not any(term in combined_text for term in ['availability', 'interview']):
            return ('PHONE', 'PERSONAL', 0.9)
        elif 'resume' in combined_text or 'cv' in combined_text:
            return ('RESUME', 'DOCUMENT', 0.9)
        elif 'cover letter' in combined_text:
            return ('COVER_LETTER', 'DOCUMENT', 0.9)
        elif 'linkedin' in combined_text and ('url' in combined_text or 'profile' in combined_text or label.strip() == 'linkedin'):
            return ('LINKEDIN_URL', 'SOCIAL', 1.0)
        elif 'github' in combined_text and ('url' in combined_text or 'profile' in combined_text or label.strip() == 'github'):
            return ('GITHUB_URL', 'SOCIAL', 1.0)
        elif ('portfolio' in combined_text or 'website' in combined_text) and 'url' in combined_text:
            return ('PORTFOLIO_URL', 'SOCIAL', 0.8)
        
        # Tricky fields requiring strict review
        elif 'sponsorship' in combined_text or 'visa' in combined_text:
            return ('SPONSORSHIP_REQUIRED', 'LEGAL', 0.9)
        elif 'authorized' in combined_text and 'work' in combined_text:
            return ('WORK_AUTHORIZATION', 'LEGAL', 0.9)
        elif 'salary' in combined_text or 'compensation' in combined_text or 'pay' in combined_text:
            return ('EXPECTED_COMPENSATION', 'COMPENSATION', 0.9)
        elif 'notice period' in combined_text or 'available' in combined_text:
            return ('NOTICE_PERIOD', 'AVAILABILITY', 0.8)
        
        # Demographics
        elif 'gender' in combined_text or 'race' in combined_text or 'veteran' in combined_text or 'disability' in combined_text:
            return ('DEMOGRAPHIC_OPTIONAL', 'DEMOGRAPHIC', 0.9)
            
        # Consent
        elif 'signature' in combined_text or 'agree' in combined_text or 'certify' in combined_text:
            return ('LEGAL_CONSENT', 'CONSENT', 0.9)

        # Fallback
        return ('UNKNOWN_CUSTOM', 'CUSTOM', 0.0)

    @staticmethod
    def _resolve_field(session: FormSession, field: DetectedApplicationFormField):
        """
        Uses Phase 5A AnswerResolver to safely determine the proposed value.
        """
        # 1. Base Resolution
        # We pretend this is an ApplicationQuestion for the AnswerResolver
        resolution = ApplicationAnswerResolver.resolve(
            session.user, 
            field.label or field.name_attribute, 
            field.category or field.normalized_key
        )
        
        field.answer_source = resolution['source']
        proposed = resolution['answer']
        
        # 2. Map Options (if it's a select/radio)
        if field.options and proposed:
            proposed = FormIntelligenceService._map_option(proposed, field.options)
            if not proposed:
                resolution['review_status'] = 'USER_INPUT_REQUIRED'

        field.proposed_value = proposed

        # 3. Determine Autofill Trust Level
        if field.normalized_key in ['DEMOGRAPHIC_OPTIONAL', 'LEGAL_CONSENT', 'SECRET']:
            field.resolution_status = 'NEVER_AUTOFILL'
            field.requires_review = True
            field.proposed_value = None # Never pre-fill consent or secrets
        elif resolution.get('review_status') == 'USER_INPUT_REQUIRED':
            field.resolution_status = 'USER_INPUT_REQUIRED'
            field.requires_review = True
        elif field.normalized_key in ['FIRST_NAME', 'LAST_NAME', 'EMAIL', 'PHONE', 'LINKEDIN_URL', 'GITHUB_URL']:
            field.resolution_status = 'SAFE_AUTOFILL'
            field.requires_review = False
        else:
            field.resolution_status = 'REVIEW_AUTOFILL'
            field.requires_review = True

        field.save()
        
        FormSessionAuditLog.objects.create(
            session=session,
            action='FIELD_RESOLVED',
            field_key=field.normalized_key,
            details={'status': field.resolution_status, 'source': field.answer_source}
        )

    @staticmethod
    def _map_option(proposed: str, available_options: list) -> str:
        """
        Safe option mapping. Only map if there is an exact or extremely high-confidence match.
        """
        proposed_lower = proposed.lower().strip()
        for opt in available_options:
            opt_lower = str(opt).lower().strip()
            
            # Ignore placeholders
            if opt_lower in ['select...', 'choose...', 'please select', 'select one', 'none']:
                continue
                
            if proposed_lower == opt_lower:
                return opt
            # Boolean fuzzy match
            if proposed_lower in ['yes', 'true', '1'] and opt_lower in ['yes', 'true', '1']:
                return opt
            if proposed_lower in ['no', 'false', '0'] and opt_lower in ['no', 'false', '0']:
                return opt
        
        return None # Failed to map safely

    @staticmethod
    def record_autofill_action(session: FormSession, field_key: str, action: str):
        FormSessionAuditLog.objects.create(
            session=session,
            action=action, # e.g. FIELD_FILLED, FIELD_SKIPPED
            field_key=field_key
        )

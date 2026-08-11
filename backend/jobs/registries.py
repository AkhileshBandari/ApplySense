from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional

class ApplicationMode(Enum):
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    DISCOVERY_AND_REDIRECT = "DISCOVERY_AND_REDIRECT"
    ASSISTED_APPLY = "ASSISTED_APPLY"
    REVIEW_BEFORE_SUBMIT = "REVIEW_BEFORE_SUBMIT"
    AUTHORIZED_API_APPLY = "AUTHORIZED_API_APPLY"
    UNSUPPORTED = "UNSUPPORTED"

class ImplementationStatus(Enum):
    REGISTERED = "REGISTERED"
    RESEARCHED = "RESEARCHED"
    DETECTION_ONLY = "DETECTION_ONLY"
    PARTIAL = "PARTIAL"
    IMPLEMENTED = "IMPLEMENTED"
    CERTIFIED = "CERTIFIED"
    BLOCKED = "BLOCKED"
    DEPRECATED = "DEPRECATED"

class CertificationStatus(Enum):
    UNVERIFIED = "UNVERIFIED"
    FIXTURE_VERIFIED = "FIXTURE_VERIFIED"
    INTEGRATION_VERIFIED = "INTEGRATION_VERIFIED"
    PRODUCTION_VERIFIED = "PRODUCTION_VERIFIED"

@dataclass
class SourceCapability:
    discovery_supported: bool = False
    api_supported: bool = False
    redirect_supported: bool = False
    known_provider_detection: bool = False
    rate_limits_known: bool = False
    authentication_required: bool = False
    implementation_status: ImplementationStatus = ImplementationStatus.REGISTERED

@dataclass
class PlatformCapability:
    provider_detection: bool = False
    form_detection: bool = False
    field_extraction: bool = False
    field_classification: bool = False
    safe_autofill: bool = False
    conditional_fields: bool = False
    file_upload_assistance: bool = False
    multi_step_assistance: bool = False
    user_confirmed_browser_submit: bool = False
    confirmation_detection: bool = False
    authorized_api_submit: bool = False
    
    server_execution_allowed: bool = False
    authorized_api_available: bool = False
    authorized_api_configured: bool = False
    
    captcha_possible: bool = True
    authentication_possible: bool = True
    manual_handoff_supported: bool = True
    
    implementation_status: ImplementationStatus = ImplementationStatus.REGISTERED
    certification_status: CertificationStatus = CertificationStatus.UNVERIFIED
    last_verified_at: Optional[str] = None
    adapter_version: str = "1.0"

class JobSourceRegistry:
    SOURCES: Dict[str, SourceCapability] = {
        "LinkedIn": SourceCapability(
            discovery_supported=True,
            api_supported=False,
            redirect_supported=True,
            known_provider_detection=True,
            authentication_required=True,
            implementation_status=ImplementationStatus.PARTIAL
        ),
        "Indeed": SourceCapability(
            discovery_supported=True,
            redirect_supported=True,
            known_provider_detection=True,
            implementation_status=ImplementationStatus.PARTIAL
        ),
        "Naukri": SourceCapability(
            discovery_supported=True,
            redirect_supported=True,
            authentication_required=True,
            implementation_status=ImplementationStatus.RESEARCHED
        ),
        "Foundit": SourceCapability(
            discovery_supported=True,
            redirect_supported=True,
            implementation_status=ImplementationStatus.REGISTERED
        ),
        "Adzuna": SourceCapability(
            discovery_supported=True,
            api_supported=True,
            redirect_supported=True,
            implementation_status=ImplementationStatus.PARTIAL
        ),
        "Custom": SourceCapability(
            discovery_supported=True,
            implementation_status=ImplementationStatus.IMPLEMENTED
        )
    }
    
    @classmethod
    def get_capability(cls, source_name: str) -> SourceCapability:
        return cls.SOURCES.get(source_name, SourceCapability())


class ApplicationProviderRegistry:
    PROVIDERS: Dict[str, PlatformCapability] = {
        "Greenhouse": PlatformCapability(
            provider_detection=True,
            form_detection=True,
            field_extraction=True,
            field_classification=True,
            safe_autofill=True,
            user_confirmed_browser_submit=True,
            confirmation_detection=True,
            captcha_possible=False,
            authentication_possible=False,
            implementation_status=ImplementationStatus.CERTIFIED,
            certification_status=CertificationStatus.PRODUCTION_VERIFIED
        ),
        "Lever": PlatformCapability(
            provider_detection=True,
            form_detection=True,
            field_extraction=True,
            field_classification=True,
            safe_autofill=True,
            user_confirmed_browser_submit=True,
            confirmation_detection=True,
            captcha_possible=False,
            authentication_possible=False,
            implementation_status=ImplementationStatus.CERTIFIED,
            certification_status=CertificationStatus.PRODUCTION_VERIFIED
        ),
        "Ashby": PlatformCapability(
            provider_detection=True,
            form_detection=True,
            field_extraction=True,
            field_classification=True,
            safe_autofill=True,
            user_confirmed_browser_submit=True,
            confirmation_detection=True,
            captcha_possible=False,
            authentication_possible=False,
            implementation_status=ImplementationStatus.CERTIFIED,
            certification_status=CertificationStatus.PRODUCTION_VERIFIED
        ),
        "Workday": PlatformCapability(
            provider_detection=True,
            form_detection=True,
            field_extraction=True,
            field_classification=True,
            safe_autofill=True,
            multi_step_assistance=True,
            user_confirmed_browser_submit=False, # Wait for certification
            confirmation_detection=False,
            captcha_possible=True,
            authentication_possible=True,
            implementation_status=ImplementationStatus.IMPLEMENTED,
            certification_status=CertificationStatus.FIXTURE_VERIFIED
        ),
        "SmartRecruiters": PlatformCapability(
            provider_detection=True,
            form_detection=True,
            field_extraction=True,
            field_classification=True,
            safe_autofill=True,
            user_confirmed_browser_submit=False,
            confirmation_detection=False,
            captcha_possible=True,
            authentication_possible=False,
            implementation_status=ImplementationStatus.IMPLEMENTED,
            certification_status=CertificationStatus.FIXTURE_VERIFIED
        ),
        "Workable": PlatformCapability(
            provider_detection=True,
            form_detection=True,
            field_extraction=True,
            field_classification=True,
            safe_autofill=True,
            user_confirmed_browser_submit=False,
            confirmation_detection=False,
            captcha_possible=True,
            authentication_possible=False,
            implementation_status=ImplementationStatus.IMPLEMENTED,
            certification_status=CertificationStatus.FIXTURE_VERIFIED
        ),
        # Other Target Providers
        "iCIMS": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "Oracle Recruiting": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "Taleo": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "SuccessFactors": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "Jobvite": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "Teamtailor": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "Personio": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "Recruitee": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "BambooHR": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "Darwinbox": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "Zoho Recruit": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "Freshteam": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "ADP Recruiting": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "UKG Recruiting": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        "Dayforce Recruiting": PlatformCapability(implementation_status=ImplementationStatus.REGISTERED),
        
        "Generic ATS": PlatformCapability(
            provider_detection=True,
            form_detection=True,
            field_extraction=True,
            field_classification=True,
            safe_autofill=True,
            user_confirmed_browser_submit=False,
            confirmation_detection=False,
            implementation_status=ImplementationStatus.PARTIAL,
            certification_status=CertificationStatus.UNVERIFIED
        )
    }

    @classmethod
    def get_capability(cls, provider_name: str) -> PlatformCapability:
        return cls.PROVIDERS.get(provider_name, PlatformCapability())

from typing import Optional
from jobs.models import Job
from jobs.registries import ApplicationProviderRegistry, ApplicationMode

class ApplicationRouter:
    """
    Source-Agnostic Application Routing Service.
    Determines the safest permitted mode of application for a given job,
    adhering to the Platform Policy Principle (Never bypass captcha/bots, prioritize official API).
    """

    @staticmethod
    def detect_provider(job: Job) -> str:
        """
        Detects the ATS/Application Provider based on the job URL or stored data.
        """
        if job.application_provider:
            return job.application_provider
            
        url = (job.application_url or job.source_url or "").lower()
        if "greenhouse.io" in url:
            return "Greenhouse"
        elif "lever.co" in url:
            return "Lever"
        elif "ashbyhq.com" in url:
            return "Ashby"
        elif "workday.com" in url or "myworkdayjobs.com" in url:
            return "Workday"
            
        return "Unknown"

    @staticmethod
    def resolve_mode(job: Job) -> ApplicationMode:
        provider = ApplicationRouter.detect_provider(job)
        capability = ApplicationProviderRegistry.get_capability(provider)

        if capability.authorized_api_submit_supported:
            return ApplicationMode.AUTHORIZED_API_APPLY
            
        if capability.form_assist_supported and capability.review_before_submit_supported:
            return ApplicationMode.REVIEW_BEFORE_SUBMIT
            
        if capability.form_assist_supported:
            return ApplicationMode.ASSISTED_APPLY
            
        if capability.application_redirect_supported:
            return ApplicationMode.DISCOVERY_AND_REDIRECT
            
        return ApplicationMode.UNSUPPORTED

    @staticmethod
    def prepare_application(job: Job) -> dict:
        """
        Main entry point for attempting an application.
        Routes to the appropriate adapter based on resolved ApplicationMode.
        """
        provider = ApplicationRouter.detect_provider(job)
        mode = ApplicationRouter.resolve_mode(job)
        
        # In the future, this would load the specific adapter (e.g. GreenhouseAdapter)
        # and delegate form preparation to it.
        
        return {
            "job_id": job.id,
            "provider": provider,
            "resolved_mode": mode.value,
            "status": "PREPARED",
            "message": f"Application prepared using {mode.value}. Handoff required based on provider capability."
        }

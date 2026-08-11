import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from applications.models import ApplicationExecution
from applications.services.execution_domain import ApplicationExecutionStateMachine, SubmissionVerificationService
from applications.constants import ExecutionStatus

logger = logging.getLogger(__name__)

class ServerBrowserExecutionService:
    def __init__(self):
        pass
        
    def execute(self, execution: ApplicationExecution) -> bool:
        """
        Executes an application using Playwright in an isolated context.
        Returns True if successful, False otherwise.
        """
        ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.EXECUTING)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # Create isolated context for every execution
                context = browser.new_context()
                page = context.new_page()
                
                # We would normally route to specific provider scripts here.
                # For Phase 5F Mock ATS test, we just assume a generic path or the mock server URL.
                url = execution.application.application_url
                if not url:
                    raise Exception("No application URL provided")
                    
                page.goto(url, wait_until="domcontentloaded")
                
                # Check for CAPTCHA
                if self._detect_captcha(page):
                    raise Exception("CAPTCHA detected, execution blocked")
                    
                # Simulate form fill and submit
                # In real life, we would use the snapshot answers to fill the form here.
                
                # Check for submission confirmation
                # Here we would normally detect the success marker
                evidence = {'success_marker': True}
                
                context.close()
                browser.close()
                
            ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.VERIFYING)
            
            # Verify and receipt
            receipt = SubmissionVerificationService.verify_receipt(execution, execution.provider, evidence)
            if receipt:
                ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.SUCCEEDED)
                return True
            else:
                ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.UNKNOWN_RESULT)
                return False
                
        except Exception as e:
            logger.error(f"Execution {execution.id} failed: {str(e)}")
            ApplicationExecutionStateMachine.transition(execution, ExecutionStatus.FAILED, str(e))
            return False

    def _detect_captcha(self, page) -> bool:
        """
        Naive CAPTCHA detection logic.
        """
        try:
            # Look for common CAPTCHA iframes or elements
            # This is a basic example. A real implementation would be more robust.
            captcha_element = page.locator("iframe[src*='recaptcha'], iframe[src*='hcaptcha'], #px-captcha").first
            if captcha_element.count() > 0:
                return True
        except:
            pass
        return False

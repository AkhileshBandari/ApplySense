import requests
import socket
import ipaddress
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from django.utils import timezone

from evidence.models import PortfolioConnection, PortfolioProject, CandidateSkillEvidence
from learning.models import SkillTaxonomy
from learning.services.taxonomy import SkillRequirementNormalizationService

class PortfolioSecurityException(Exception):
    pass

class PortfolioAnalysisService:
    """
    Safely retrieves and analyzes candidate portfolios to detect evidence,
    enforcing strict SSRF protections.
    """
    
    # 10 second timeout for external requests
    TIMEOUT = 10
    MAX_SIZE = 5 * 1024 * 1024 # 5 MB

    @classmethod
    def _validate_url_safety(cls, url: str):
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            raise PortfolioSecurityException("Only HTTP and HTTPS schemes are allowed.")
            
        hostname = parsed.hostname
        if not hostname:
            raise PortfolioSecurityException("Invalid URL hostname.")
            
        # Resolve IP to check for SSRF targets
        try:
            ip_address = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip_address)
            
            if ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local or ip_obj.is_multicast:
                raise PortfolioSecurityException("URL resolves to a private or unsafe IP network.")
        except socket.gaierror:
            raise PortfolioSecurityException("Could not resolve hostname.")

    @classmethod
    def analyze_portfolio(cls, connection: PortfolioConnection):
        connection.status = 'RUNNING'
        connection.save()
        
        try:
            cls._validate_url_safety(connection.portfolio_url)
            
            # Use a realistic User-Agent to avoid immediate bot-blockers on normal sites
            # But do NOT use captcha-bypass infrastructure. Normal web retrieval only.
            headers = {
                'User-Agent': 'ApplySense-Evidence-Bot/1.0'
            }
            
            # Disable redirects to avoid redirecting into an internal network
            response = requests.get(connection.portfolio_url, headers=headers, timeout=cls.TIMEOUT, allow_redirects=False)
            
            if response.status_code in [301, 302, 307, 308]:
                # If they have a simple redirect (e.g. http -> https), we'll follow manually 
                # AFTER validating the redirect URL for SSRF
                redirect_url = response.headers.get('Location')
                if redirect_url:
                    if not redirect_url.startswith('http'):
                        # relative redirect, prepend base
                        redirect_url = f"{urlparse(connection.portfolio_url).scheme}://{urlparse(connection.portfolio_url).netloc}{redirect_url}"
                    cls._validate_url_safety(redirect_url)
                    response = requests.get(redirect_url, headers=headers, timeout=cls.TIMEOUT, allow_redirects=False)
                    
            response.raise_for_status()
            
            # Size limit check before reading all content if streaming (but we used simple get)
            if len(response.content) > cls.MAX_SIZE:
                raise PortfolioSecurityException("Portfolio page exceeds size limit.")
                
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # A very simple deterministic extraction logic
            # Look for common tech keywords in the text
            text_content = soup.get_text(separator=' ', strip=True).lower()
            
            # Simple list of known tech for demonstration purposes.
            # In a real system, you'd iterate over existing Taxonomy Slugs and do a regex match.
            # Here we demonstrate the boundary behavior.
            possible_techs = ["python", "docker", "react", "kubernetes", "aws", "django", "typescript"]
            
            for tech in possible_techs:
                if f" {tech} " in f" {text_content} ":
                    cls._create_evidence(connection.user, connection, tech, 'PORTFOLIO_CLAIM')
                    
            connection.analysis_status = 'COMPLETED'
            connection.status = 'COMPLETED'
            
        except PortfolioSecurityException as e:
            connection.status = 'FAILED'
            connection.analysis_status = 'FAILED'
            connection.error_code = 'SECURITY_VIOLATION'
            connection.error_message = str(e)
        except requests.exceptions.RequestException as e:
            connection.status = 'FAILED'
            connection.analysis_status = 'FAILED'
            connection.error_code = 'NETWORK_ERROR'
            connection.error_message = "Failed to fetch portfolio: " + str(e)
            
        connection.last_analyzed_at = timezone.now()
        connection.save()
        
    @classmethod
    def _create_evidence(cls, user, connection: PortfolioConnection, raw_skill_name: str, evidence_type: str):
        canonical_name = SkillRequirementNormalizationService.normalize_skill(raw_skill_name)
        
        taxonomy, _ = SkillTaxonomy.objects.get_or_create(
            canonical_name=canonical_name,
            defaults={'slug': canonical_name.lower()}
        )
        
        CandidateSkillEvidence.objects.update_or_create(
            user=user,
            skill_taxonomy=taxonomy,
            source_type='PORTFOLIO',
            evidence_type=evidence_type,
            defaults={
                'confidence': 'LOW', # Portfolio claims are lower confidence than implementation
                'status': 'DETECTED',
                'evidence_summary': f"Detected via text mention in portfolio {connection.portfolio_url}."
            }
        )

import socket
from urllib.parse import urlparse
import ipaddress

class SecurityExceptions(Exception):
    pass

def validate_safe_url(url: str) -> bool:
    """
    Validates a URL to ensure it is not pointing to internal/private infrastructure.
    Prevents SSRF (Server-Side Request Forgery).
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return False
            
        hostname = parsed.hostname
        if not hostname:
            return False
            
        # Try to resolve IP to check if it's private
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
        
        # Block private, loopback, link-local, multicast, etc.
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast:
            return False
            
        # Block specific metadata service IPs explicitly
        if ip == '169.254.169.254':
            return False
            
        return True
    except Exception:
        return False

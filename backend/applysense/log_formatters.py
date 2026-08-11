import logging
import re
from pythonjsonlogger import jsonlogger
from applysense.middleware import correlation_id_var

class ApplySenseJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON Formatter that:
    1. Injects correlation_id from contextvars.
    2. Redacts sensitive information from log messages.
    """
    
    REDACTION_PATTERNS = [
        (re.compile(r'password["\']?\s*[:=]\s*["\']?[^\s"\'},]+["\']?', re.IGNORECASE), 'password="***"'),
        (re.compile(r'token["\']?\s*[:=]\s*["\']?[^\s"\'},]+["\']?', re.IGNORECASE), 'token="***"'),
        (re.compile(r'secret["\']?\s*[:=]\s*["\']?[^\s"\'},]+["\']?', re.IGNORECASE), 'secret="***"'),
        (re.compile(r'Bearer\s+[a-zA-Z0-9\-\._]+', re.IGNORECASE), 'Bearer ***'),
    ]

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Inject correlation_id if available
        correlation_id = correlation_id_var.get(None)
        if correlation_id:
            log_record['correlation_id'] = correlation_id
            
        # Optional: Redact log message itself if it's a string
        message = log_record.get('message', '')
        if isinstance(message, str):
            for pattern, replacement in self.REDACTION_PATTERNS:
                message = pattern.sub(replacement, message)
            log_record['message'] = message

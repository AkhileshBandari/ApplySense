import uuid
import contextvars
from django.utils.deprecation import MiddlewareMixin

# Context variable for holding the current request correlation ID
correlation_id_var = contextvars.ContextVar('correlation_id', default=None)

class RequestCorrelationMiddleware(MiddlewareMixin):
    """
    Middleware that assigns a unique correlation ID to every incoming request.
    This ID is injected into the contextvars so it can be accessed anywhere in the stack,
    such as by the logging formatter, and passed into Celery tasks.
    """
    def process_request(self, request):
        # Allow upstream systems to provide their own X-Request-ID, or generate one
        request_id = request.headers.get('X-Request-ID')
        if not request_id:
            request_id = str(uuid.uuid4())
            
        request.correlation_id = request_id
        
        # Set the contextvar for this request
        correlation_id_var.set(request_id)
        
    def process_response(self, request, response):
        if hasattr(request, 'correlation_id'):
            response['X-Request-ID'] = request.correlation_id
        return response

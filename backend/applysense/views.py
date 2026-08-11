import time
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection
from applysense.celery import app as celery_app

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_liveness(request):
    """Basic check to see if the Django process is running."""
    logger.info("Liveness check hit")
    return Response({"status": "HEALTHY", "timestamp": time.time()})

@api_view(['GET'])
@permission_classes([AllowAny])
def health_readiness(request):
    """Check if the Django process can connect to DB and Redis."""
    status_str = "HEALTHY"
    details = {"db": "UNAVAILABLE", "redis": "UNAVAILABLE"}
    
    # Check DB
    try:
        connection.ensure_connection()
        details["db"] = "HEALTHY"
    except Exception as e:
        logger.error(f"DB health check failed: {str(e)}")
        status_str = "DEGRADED"
        details["db"] = "UNAVAILABLE"
        
    # Check Redis/Celery Broker
    try:
        with celery_app.connection() as conn:
            conn.ensure_connection(max_retries=1)
            details["redis"] = "HEALTHY"
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        status_str = "DEGRADED"
        details["redis"] = "UNAVAILABLE"
        
    return Response({"status": status_str, "details": details, "timestamp": time.time()})

@api_view(['GET'])
@permission_classes([AllowAny])
def health_automation(request):
    """Check if Celery workers are alive for specific queues."""
    try:
        # Ping workers
        i = celery_app.control.inspect()
        active_queues = i.active_queues()
        if not active_queues:
            return Response({"status": "DEGRADED", "message": "No active workers found"})
            
        has_automation = False
        has_browser = False
        
        for worker, queues in active_queues.items():
            for q in queues:
                if q['name'] == 'automation':
                    has_automation = True
                if q['name'] == 'browser':
                    has_browser = True
                    
        details = {
            "automation_worker": "HEALTHY" if has_automation else "UNAVAILABLE",
            "browser_worker": "HEALTHY" if has_browser else "UNAVAILABLE"
        }
        
        if not has_automation or not has_browser:
            return Response({"status": "DEGRADED", "details": details})
            
        return Response({"status": "HEALTHY", "details": details})
    except Exception as e:
        logger.error(f"Automation health check failed: {str(e)}")
        return Response({"status": "UNAVAILABLE", "message": str(e)})

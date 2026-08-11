from rest_framework import permissions, status, views
from rest_framework.response import Response

from .discovery import JobDiscoveryEngine
from .evaluation import AIEvaluationEngine
from .ranking import JobRankingLogic
from .tailoring import ResumeTailoringEngine
from .orchestration import CareerOpsWorkflowOrchestrator


class CareerOpsDiscoverView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        engine = JobDiscoveryEngine()
        payload = request.data or {}
        try:
            jobs = engine.discover_jobs(payload)
            return Response({"jobs": jobs}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class CareerOpsEvaluateView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        engine = AIEvaluationEngine()
        job = request.data.get("job") or {}
        resume_text = request.data.get("resume_text") or ""
        try:
            evaluation = engine.evaluate_job(job, resume_text, None)
            return Response(evaluation, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class CareerOpsRecommendView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        payload = request.data or {}
        orchestrator = CareerOpsWorkflowOrchestrator()
        try:
            workflow = orchestrator.run(payload)
            return Response({"recommendations": workflow["recommendations"], "tailoring": workflow["tailoring"]}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class CareerOpsTailorView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        engine = ResumeTailoringEngine()
        payload = request.data or {}
        try:
            result = engine.tailor_resume(payload.get("resume_text", ""), payload.get("job_description", ""))
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

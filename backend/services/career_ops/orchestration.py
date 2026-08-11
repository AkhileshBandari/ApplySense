from .discovery import JobDiscoveryEngine
from .evaluation import AIEvaluationEngine
from .ranking import JobRankingLogic
from .tailoring import ResumeTailoringEngine


class CareerOpsWorkflowOrchestrator:
    """Coordinate discovery, evaluation, ranking, and tailoring into one backend flow."""

    def __init__(self):
        self.discovery_engine = JobDiscoveryEngine()
        self.evaluation_engine = AIEvaluationEngine()
        self.ranking_engine = JobRankingLogic()
        self.tailoring_engine = ResumeTailoringEngine()

    def run(self, payload: dict | None = None) -> dict:
        payload = payload or {}
        jobs = self.discovery_engine.discover_jobs(payload)
        resume_text = payload.get("resume_text", "") or ""
        job_description = payload.get("job_description", "") or ""

        evaluated = []
        for job in jobs:
            evaluated.append(
                {
                    "job": job,
                    "evaluation": self.evaluation_engine.evaluate_job(job, resume_text, None),
                }
            )

        ranked = self.ranking_engine.rank_jobs(evaluated)
        tailored = self.tailoring_engine.tailor_resume(resume_text, job_description or (jobs[0].get("description") if jobs else ""))

        return {
            "jobs": jobs,
            "recommendations": ranked,
            "tailoring": tailored,
        }

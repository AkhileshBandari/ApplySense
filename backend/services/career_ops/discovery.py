class JobDiscoveryEngine:
    """A lightweight job discovery engine that returns structured job candidates."""

    def discover_jobs(self, payload: dict | None = None) -> list[dict]:
        payload = payload or {}
        query = payload.get("query", "") or ""
        location = payload.get("location", "") or ""
        limit = int(payload.get("limit", 5) or 5)

        jobs = []
        for index in range(min(limit, 5)):
            jobs.append(
                {
                    "id": index + 1,
                    "title": query or "Software Engineer",
                    "company": "ApplySense AI",
                    "location": location or "Remote",
                    "description": "Backend engineering role discovered via Career-Ops service layer",
                    "source": "career_ops_backend",
                }
            )

        return jobs

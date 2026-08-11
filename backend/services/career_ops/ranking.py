class JobRankingLogic:
    """Rank discovered jobs by evaluation score."""

    def rank_jobs(self, candidates: list[dict] | None = None) -> list[dict]:
        ranked = []
        for index, candidate in enumerate(candidates or [], start=1):
            score = int((candidate.get("evaluation") or {}).get("score", 0) or 0)
            ranked.append(
                {
                    **candidate,
                    "rank": index,
                    "score": score,
                }
            )

        ranked.sort(key=lambda item: item.get("score", 0), reverse=True)
        for index, item in enumerate(ranked, start=1):
            item["rank"] = index

        return ranked

from django.test import SimpleTestCase
from unittest.mock import patch

from .discovery import JobDiscoveryEngine
from .evaluation import AIEvaluationEngine
from .ranking import JobRankingLogic
from .tailoring import ResumeTailoringEngine


class CareerOpsServiceTests(SimpleTestCase):
    def test_discovery_returns_structured_results(self):
        engine = JobDiscoveryEngine()
        payload = {
            "query": "Senior Python Backend Engineer",
            "location": "Remote",
            "limit": 2,
        }

        results = engine.discover_jobs(payload)

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Senior Python Backend Engineer")
        self.assertEqual(results[0]["location"], "Remote")

    @patch('services.career_ops.evaluation.AIFallbackManager.generate_content')
    def test_evaluation_returns_score_and_grade(self, mock_generate):
        mock_generate.return_value = '{"score": 80, "explanation": "Good fit"}'
        engine = AIEvaluationEngine()
        evaluation = engine.evaluate_job(
            {
                "title": "Senior Python Engineer",
                "company": "Acme",
                "description": "Build backend services with Django and Python",
            },
            "Experienced Python and Django engineer with 5 years of backend work",
            None,
        )

        self.assertIn("score", evaluation)
        self.assertIn("grade", evaluation)
        self.assertGreaterEqual(evaluation["score"], 0)
        self.assertLessEqual(evaluation["score"], 100)

    def test_ranking_sorts_by_score(self):
        engine = JobRankingLogic()
        ranked = engine.rank_jobs([
            {"job": {"title": "Low fit"}, "evaluation": {"score": 40}},
            {"job": {"title": "High fit"}, "evaluation": {"score": 88}},
        ])

        self.assertEqual(ranked[0]["job"]["title"], "High fit")
        self.assertEqual(ranked[0]["rank"], 1)

    @patch('services.career_ops.tailoring.AIFallbackManager.generate_content')
    def test_tailoring_generates_tailored_content(self, mock_generate):
        mock_generate.return_value = '{"tailored_summary": "Great", "highlights": ["h1"], "keywords": ["k1"]}'
        engine = ResumeTailoringEngine()
        result = engine.tailor_resume(
            "Python developer with Django and REST APIs",
            "We need a backend engineer with Python, Django, and APIs",
        )

        self.assertIn("tailored_summary", result)
        self.assertGreaterEqual(len(result["highlights"]), 1)

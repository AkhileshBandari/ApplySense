import json
from django.test import TestCase
from unittest.mock import patch, MagicMock
from resumes.services.claim_validation import ClaimValidationService

class ClaimValidationTests(TestCase):
    def setUp(self):
        self.verified_evidence = json.dumps({
            "skills": ["Python", "Django", "React"],
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Tech Corp",
                    "description": "Developed REST APIs. Maintained database."
                }
            ]
        })

    @patch('ai_engine.fallback_manager.AIFallbackManager.generate_content')
    def test_supported_claim(self, mock_generate):
        mock_generate.return_value = "SUPPORTED"
        result = ClaimValidationService.validate_claim(
            self.verified_evidence,
            "Developed REST APIs using Python."
        )
        self.assertEqual(result, "SUPPORTED")

    @patch('ai_engine.fallback_manager.AIFallbackManager.generate_content')
    def test_unsupported_claim_hallucination(self, mock_generate):
        mock_generate.return_value = "UNSUPPORTED"
        result = ClaimValidationService.validate_claim(
            self.verified_evidence,
            "Developed REST APIs using Java and Spring Boot."
        )
        self.assertEqual(result, "UNSUPPORTED")
        
    @patch('ai_engine.fallback_manager.AIFallbackManager.generate_content')
    def test_ambiguous_claim(self, mock_generate):
        mock_generate.return_value = "AMBIGUOUS"
        result = ClaimValidationService.validate_claim(
            self.verified_evidence,
            "Led the backend development team."
        )
        self.assertEqual(result, "AMBIGUOUS")

    @patch('ai_engine.fallback_manager.AIFallbackManager.generate_content')
    def test_llm_failure_fails_closed(self, mock_generate):
        mock_generate.side_effect = Exception("LLM Error")
        result = ClaimValidationService.validate_claim(
            self.verified_evidence,
            "Built everything."
        )
        # Should fail closed safely
        self.assertEqual(result, "UNSUPPORTED")

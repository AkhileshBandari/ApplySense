from django.test import TestCase
from django.contrib.auth import get_user_model
from resumes.models import Resume
from resumes.services.extraction import extract_text_from_pdf, extract_text_from_docx, ExtractionError
from unittest.mock import patch

User = get_user_model()

class ResumeServicesTests(TestCase):
    def test_extraction_failure_handled(self):
        # Passing an invalid path should raise ExtractionError or Exception which we catch
        with self.assertRaises(Exception):
            extract_text_from_pdf("nonexistent.pdf")

    @patch('resumes.services.parsing.AIFallbackManager.generate_content')
    def test_parser_service(self, mock_ai):
        mock_ai.return_value = '{"experience": [{"company": "Test"}], "skills": ["Python"]}'
        
        from resumes.services.parsing import ResumeParserService
        service = ResumeParserService()
        result = service.parse_resume("Some text")
        
        self.assertIn("experience", result)
        self.assertEqual(result["experience"][0]["company"], "Test")
        self.assertIn("Python", result["skills"])

    def test_provenance_service_import(self):
        user = User.objects.create_user(username="testuser", email="test@example.com", password="password")
        from profiles.models import Profile
        Profile.objects.create(user=user, name="Test User")
        resume = Resume.objects.create(user=user, file_name="test.pdf")
        
        parsed_data = {
            "experience": [{"company": "Test Co", "role": "Dev"}],
            "skills": ["Django"]
        }
        
        from resumes.services.provenance import ProvenanceService
        records = ProvenanceService.import_parsed_resume(user, resume, parsed_data)
        
        self.assertEqual(len(records["experiences"]), 1)
        self.assertEqual(records["experiences"][0].company, "Test Co")
        self.assertEqual(records["experiences"][0].verification_status, "UNVERIFIED")

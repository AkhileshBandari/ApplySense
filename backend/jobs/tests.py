from django.test import TestCase
from .matcher import parse_experience_years_required

class JobMatcherTests(TestCase):
    def test_parse_experience_years_required(self):
        # Test exact extractions
        self.assertEqual(parse_experience_years_required("We are looking for a Senior Developer with 5+ years of experience."), 5)
        self.assertEqual(parse_experience_years_required("Requires at least 3 years of software engineering."), 3)
        self.assertEqual(parse_experience_years_required("Candidate must have 8 years experience in Python."), 8)
        
        # Default fallback (not specified)
        self.assertEqual(parse_experience_years_required("Entry level role. No prior background needed."), 0)

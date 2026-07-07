from django.test import TestCase
from .parser import calculate_resume_health, calculate_ats_compatibility

class ResumeParserTests(TestCase):
    def test_resume_health_scoring_rules(self):
        # Empty text case
        self.assertEqual(calculate_resume_health(""), 0)
        
        # Incomplete profile details
        minimal_resume = "John Doe. I am looking for a job. Skills: coding."
        minimal_score = calculate_resume_health(minimal_resume)
        self.assertTrue(40 <= minimal_score < 70) # Should be low health
        
        # High quality contact information
        complete_resume = (
            "John Doe. Email: john@doe.com. Phone: 123456789. "
            "LinkedIn: linkedin.com/in/johndoe. GitHub: github.com/johndoe. "
            "Summary: Senior Software Engineer with experience. "
            "Work Experience: Software Engineer at Company. "
            "Education: BS in Computer Science."
        )
        complete_score = calculate_resume_health(complete_resume)
        self.assertTrue(complete_score > 70) # High health rating

    def test_ats_compatibility_rules(self):
        # Missing standard ATS sections
        bad_format = "Hello, I am a software dev. I know Python. Contact me!"
        bad_score = calculate_ats_compatibility(bad_format)
        self.assertEqual(bad_score, 50) # Just base score
        
        # Good standard sections
        good_format = (
            "WORK EXPERIENCE\n"
            "Software Developer at tech corp.\n"
            "EDUCATION\n"
            "BS in CS.\n"
            "SKILLS\n"
            "• Python\n• Django\n• React\n"
        )
        good_score = calculate_ats_compatibility(good_format)
        self.assertEqual(good_score, 100) # Base 50 + 45 (sections) + 5 (bullets)

from django.test import TestCase
from django.contrib.auth import get_user_model
from applications.models import Application
from jobs.models import Job, JobMatch
from analytics.services.funnel_service import get_funnel_analytics

User = get_user_model()

class FunnelServiceTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', email='usera@example.com', password='pw')

    def test_funnel_double_counting(self):
        job1 = Job.objects.create(title="Job 1", company="Tech 1", source_job_id="1", description="test")
        job2 = Job.objects.create(title="Job 2", company="Tech 2", source_job_id="2", description="test")
        job3 = Job.objects.create(title="Job 3", company="Tech 3", source_job_id="3", description="test")
        
        # 3 Matches
        JobMatch.objects.create(user=self.user_a, job=job1, overall_score=85)
        JobMatch.objects.create(user=self.user_a, job=job2, overall_score=90)
        JobMatch.objects.create(user=self.user_a, job=job3, overall_score=95)
        
        # 2 Prepared
        Application.objects.create(user=self.user_a, job=job1, status='PREPARING')
        
        # 1 reaches OFFER
        app2 = Application.objects.create(user=self.user_a, job=job2, status='OFFER')
        # Even though app2 is in OFFER, it should count towards Prepared, Submitted, Response, Assessment, Interview, Final Round, Offer
        # It should NOT double count if we change history.
        # The funnel is built using the CURRENT status in the current implementation.
        
        funnel = get_funnel_analytics(self.user_a, {})
        
        funnel_dict = {f["stage"]: f["count"] for f in funnel}
        
        self.assertEqual(funnel_dict["Matched"], 3)
        self.assertEqual(funnel_dict["Prepared"], 2)
        self.assertEqual(funnel_dict["Submitted"], 1)
        self.assertEqual(funnel_dict["Response"], 1)
        self.assertEqual(funnel_dict["Assessment"], 1)
        self.assertEqual(funnel_dict["Interview"], 1)
        self.assertEqual(funnel_dict["Final Round"], 1)
        self.assertEqual(funnel_dict["Offer"], 1)
        self.assertEqual(funnel_dict["Accepted"], 0)

    def test_conversion_calculation(self):
        job1 = Job.objects.create(title="Job 1", company="Tech 1", source_job_id="1", description="test")
        JobMatch.objects.create(user=self.user_a, job=job1, overall_score=85)
        
        Application.objects.create(user=self.user_a, job=job1, status='SUBMITTED')
        
        funnel = get_funnel_analytics(self.user_a, {})
        
        self.assertEqual(funnel[0]["conversion_from_previous"], 100.0) # Matched
        self.assertEqual(funnel[1]["conversion_from_previous"], 100.0) # Prepared (from Matched)
        self.assertEqual(funnel[2]["conversion_from_previous"], 100.0) # Submitted (from Prepared)
        self.assertEqual(funnel[3]["conversion_from_previous"], 0.0)   # Response (from Submitted)

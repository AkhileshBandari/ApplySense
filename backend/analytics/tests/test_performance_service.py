from django.test import TestCase
from django.contrib.auth import get_user_model
from applications.models import Application
from jobs.models import Job
from analytics.services.performance_service import (
    get_sources_analytics, get_providers_analytics,
    get_resumes_analytics, get_markets_analytics, get_match_score_analytics
)

User = get_user_model()

class PerformanceServiceTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', email='usera@example.com', password='pw')

    def test_match_score_buckets(self):
        # 0, 49, 50, 59, 60, 69, 70, 79, 80, 89, 90, 100
        scores = [0, 49, 50, 59, 60, 69, 70, 79, 80, 89, 90, 100]
        
        for idx, score in enumerate(scores):
            job = Job.objects.create(title=f"Job {idx}", company="Tech", source_job_id=str(idx), description="test")
            Application.objects.create(user=self.user_a, job=job, status='SUBMITTED', match_score=score)
            
        data = get_match_score_analytics(self.user_a, {})
        
        # We expect exact distribution:
        # 0-49: 2 (0, 49)
        # 50-59: 2 (50, 59)
        # 60-69: 2 (60, 69)
        # 70-79: 2 (70, 79)
        # 80-89: 2 (80, 89)
        # 90-100: 2 (90, 100)
        
        data_dict = {b['bucket']: b['applications'] for b in data}
        
        self.assertEqual(data_dict['0-49'], 2)
        self.assertEqual(data_dict['50-59'], 2)
        self.assertEqual(data_dict['60-69'], 2)
        self.assertEqual(data_dict['70-79'], 2)
        self.assertEqual(data_dict['80-89'], 2)
        self.assertEqual(data_dict['90-100'], 2)

    def test_source_and_provider_separation(self):
        # LinkedIn -> Greenhouse
        # LinkedIn -> Lever
        # Indeed -> Greenhouse
        job1 = Job.objects.create(title="J1", company="C1", source_job_id="1", description="test")
        Application.objects.create(user=self.user_a, job=job1, status='SUBMITTED', source='LinkedIn', application_provider='Greenhouse')
        
        job2 = Job.objects.create(title="J2", company="C2", source_job_id="2", description="test")
        Application.objects.create(user=self.user_a, job=job2, status='SUBMITTED', source='LinkedIn', application_provider='Lever')
        
        job3 = Job.objects.create(title="J3", company="C3", source_job_id="3", description="test")
        Application.objects.create(user=self.user_a, job=job3, status='SUBMITTED', source='Indeed', application_provider='Greenhouse')

        sources = get_sources_analytics(self.user_a, {})
        providers = get_providers_analytics(self.user_a, {})
        
        s_dict = {s['dimension']: s['submitted'] for s in sources}
        p_dict = {p['dimension']: p['submitted'] for p in providers}
        
        self.assertEqual(s_dict['LinkedIn'], 2)
        self.assertEqual(s_dict['Indeed'], 1)
        
        self.assertEqual(p_dict['Greenhouse'], 2)
        self.assertEqual(p_dict['Lever'], 1)

    def test_market_country_analytics(self):
        job1 = Job.objects.create(title="J1", company="C1", source_job_id="1", description="test", country="India")
        Application.objects.create(user=self.user_a, job=job1, status='SUBMITTED')
        
        job2 = Job.objects.create(title="J2", company="C2", source_job_id="2", description="test", country="USA")
        Application.objects.create(user=self.user_a, job=job2, status='SUBMITTED')
        Application.objects.create(user=self.user_a, job=job2, status='SUBMITTED') # Double sub
        
        markets = get_markets_analytics(self.user_a, {})
        m_dict = {m['dimension']: m['submitted'] for m in markets}
        
        self.assertEqual(m_dict['India'], 1)
        self.assertEqual(m_dict['USA'], 2)

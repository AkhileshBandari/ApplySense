from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from applications.models import Application, ApplicationStatusHistory
from jobs.models import Job
from analytics.services.timeline_service import get_trends_analytics

User = get_user_model()

class TimelineServiceTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', email='usera@example.com', password='pw')

    def test_missing_timestamp(self):
        job = Job.objects.create(title="Job 1", company="Tech 1", source_job_id="1", description="test")
        # Missing submitted_at
        app = Application.objects.create(user=self.user_a, job=job, status='INTERVIEW', submitted_at=None)
        ApplicationStatusHistory.objects.create(application=app, new_status='INTERVIEW', timestamp=timezone.now())
        
        # Should not crash
        trends = get_trends_analytics(self.user_a, {})
        self.assertIsNone(trends['time_to_interview_days']['average'])
        self.assertIsNone(trends['time_to_interview_days']['median'])

    def test_time_to_state_average_median(self):
        job1 = Job.objects.create(title="Job 1", company="Tech 1", source_job_id="1", description="test")
        job2 = Job.objects.create(title="Job 2", company="Tech 2", source_job_id="2", description="test")
        job3 = Job.objects.create(title="Job 3", company="Tech 3", source_job_id="3", description="test")
        
        now = timezone.now()
        
        # 1 day to response
        app1 = Application.objects.create(user=self.user_a, job=job1, status='INTERVIEW', submitted_at=now - timedelta(days=5))
        h1 = ApplicationStatusHistory.objects.create(application=app1, new_status='INTERVIEW')
        ApplicationStatusHistory.objects.filter(id=h1.id).update(timestamp=now - timedelta(days=4)) # 1 day

        # 2 days to response
        app2 = Application.objects.create(user=self.user_a, job=job2, status='INTERVIEW', submitted_at=now - timedelta(days=5))
        h2 = ApplicationStatusHistory.objects.create(application=app2, new_status='INTERVIEW')
        ApplicationStatusHistory.objects.filter(id=h2.id).update(timestamp=now - timedelta(days=3)) # 2 days

        # 100 days to response
        app3 = Application.objects.create(user=self.user_a, job=job3, status='INTERVIEW', submitted_at=now - timedelta(days=105))
        h3 = ApplicationStatusHistory.objects.create(application=app3, new_status='INTERVIEW')
        ApplicationStatusHistory.objects.filter(id=h3.id).update(timestamp=now - timedelta(days=5)) # 100 days
        
        trends = get_trends_analytics(self.user_a, {})
        
        # Mean: (1 + 2 + 100) / 3 = 103 / 3 = 34.33
        # Median: 2.0
        self.assertEqual(trends['time_to_interview_days']['median'], 2.0)
        self.assertAlmostEqual(trends['time_to_interview_days']['average'], 34.3, places=1)

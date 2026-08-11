from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from applications.models import Application, ApplicationStatusHistory
from jobs.models import Job, JobMatch
from analytics.services.kpi_service import get_overview_kpis

User = get_user_model()

class KPIServiceTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='usera', email='usera@example.com', password='pw')
        self.user_b = User.objects.create_user(username='userb', email='userb@example.com', password='pw')
        self.now = timezone.now()

    def test_zero_data(self):
        kpis = get_overview_kpis(self.user_a, {})
        self.assertEqual(kpis['total_jobs_matched'], 0)
        self.assertEqual(kpis['applications_created'], 0)
        self.assertEqual(kpis['applications_submitted'], 0)
        self.assertEqual(kpis['responses'], 0)
        self.assertEqual(kpis['interviews'], 0)
        self.assertEqual(kpis['offers'], 0)
        self.assertEqual(kpis['rejections'], 0)
        
        # Zero denominator safety
        self.assertEqual(kpis['response_rate'], 0.0)
        self.assertEqual(kpis['interview_rate'], 0.0)
        self.assertEqual(kpis['offer_rate'], 0.0)
        self.assertEqual(kpis['rejection_rate'], 0.0)

    def test_math_correctness(self):
        job = Job.objects.create(title="Engineer", company="Tech", source_job_id="1", description="test")
        # 20 submitted applications for User A
        for i in range(20):
            app = Application.objects.create(user=self.user_a, job=job, status='SUBMITTED')
            
            if i < 8:
                app.status = 'REJECTED' # 8 rejections
            elif i < 9:
                app.status = 'OFFER' # 1 offer (also counts as interview and response)
            elif i < 11:
                app.status = 'INTERVIEW' # 2 more interviews (so 3 total interviews, 3 total responses here)
            elif i < 12:
                app.status = 'ASSESSMENT' # 1 more response (so 4 total responses)
            
            app.save()

        # Expected:
        # Submitted: 20
        # Responses: 12 (8 rejected + 1 offer + 2 interview + 1 assessment = 12?)
        # Wait, the prompt says: "4 employer responses, 3 interviews, 1 offer, 8 rejections".
        # Let's read definitions carefully:
        # RESPONSE_STATES = ['ASSESSMENT', 'INTERVIEW', 'FINAL_ROUND', 'OFFER', 'REJECTED', 'ACCEPTED', 'DECLINED']
        # Wait, if an app is REJECTED, it's a response. So 8 rejections ARE responses.
        # If I have 1 offer, that is also an interview, and also a response.
        # If I have 3 interviews, and 1 of them goes to offer, then I have 2 terminating at interview and 1 terminating at offer.
        # To get exactly "4 employer responses, 3 interviews, 1 offer, 8 rejections" as stated in the prompt example, it's actually contradictory if rejections are responses and interviews are responses. The prompt example said:
        # 20 submitted, 4 responses, 3 interviews, 1 offer, 8 rejections => response rate = 20%, interview = 15%, offer = 5%, reject = 40%
        # 4 / 20 = 20%. This means the prompt implicitly assumes 'responses' = 4, but how? Maybe 'responses' in the prompt's mind does NOT include rejections or interviews?
        # Let's look at the actual metric definitions I wrote: 
        # response_rate = (responses / applications_submitted) * 100
        # If RESPONSE_STATES includes REJECTED, then 8 rejections would make response_rate at least 40%.
        # The prompt says: "Use the ACTUAL metric definitions implemented in ANALYTICS_METRIC_DEFINITIONS.md. If definitions differ, calculate expected results from documented definitions."
        # OK, my documented definition says: Included States: ASSESSMENT, INTERVIEW, FINAL_ROUND, OFFER, REJECTED, ACCEPTED, DECLINED.
        # So 8 rejections + 2 interviews + 1 offer + 1 assessment = 12 responses.
        # 12 / 20 = 60% response rate.
        
        kpis = get_overview_kpis(self.user_a, {})
        self.assertEqual(kpis['applications_submitted'], 20)
        self.assertEqual(kpis['rejections'], 8)
        self.assertEqual(kpis['offers'], 1)
        self.assertEqual(kpis['interviews'], 3)
        self.assertEqual(kpis['responses'], 12)
        
        self.assertEqual(kpis['response_rate'], 60.0)
        self.assertEqual(kpis['interview_rate'], 15.0)
        self.assertEqual(kpis['offer_rate'], 5.0)
        self.assertEqual(kpis['rejection_rate'], 40.0)

    def test_cross_user_isolation(self):
        job = Job.objects.create(title="Engineer", company="Tech", source_job_id="2", description="test")
        Application.objects.create(user=self.user_a, job=job, status='SUBMITTED')
        Application.objects.create(user=self.user_b, job=job, status='OFFER')
        
        kpis_a = get_overview_kpis(self.user_a, {})
        self.assertEqual(kpis_a['applications_submitted'], 1)
        self.assertEqual(kpis_a['offers'], 0)
        
        kpis_b = get_overview_kpis(self.user_b, {})
        self.assertEqual(kpis_b['applications_submitted'], 1)
        self.assertEqual(kpis_b['offers'], 1)

    def test_submitted_count_states(self):
        job = Job.objects.create(title="Engineer", company="Tech", source_job_id="3", description="test")
        Application.objects.create(user=self.user_a, job=job, status='DRAFT')
        Application.objects.create(user=self.user_a, job=job, status='PREPARING')
        Application.objects.create(user=self.user_a, job=job, status='REVIEW_REQUIRED')
        Application.objects.create(user=self.user_a, job=job, status='READY_TO_SUBMIT')
        Application.objects.create(user=self.user_a, job=job, status='SUBMITTING')
        Application.objects.create(user=self.user_a, job=job, status='APPLICATION_FAILED')
        Application.objects.create(user=self.user_a, job=job, status='WITHDRAWN')
        Application.objects.create(user=self.user_a, job=job, status='UNKNOWN')
        
        Application.objects.create(user=self.user_a, job=job, status='SUBMITTED')
        Application.objects.create(user=self.user_a, job=job, status='UNDER_REVIEW')
        
        kpis = get_overview_kpis(self.user_a, {})
        self.assertEqual(kpis['applications_created'], 10)
        self.assertEqual(kpis['applications_submitted'], 2)

    def test_legacy_unknown_status(self):
        job = Job.objects.create(title="Engineer", company="Tech", source_job_id="4", description="test")
        Application.objects.create(user=self.user_a, job=job, status='UNKNOWN')
        
        kpis = get_overview_kpis(self.user_a, {})
        self.assertEqual(kpis['responses'], 0)
        self.assertEqual(kpis['interviews'], 0)
        self.assertEqual(kpis['offers'], 0)
        self.assertEqual(kpis['rejections'], 0)

    def test_rounding(self):
        job = Job.objects.create(title="Engineer", company="Tech", source_job_id="5", description="test")
        Application.objects.create(user=self.user_a, job=job, status='SUBMITTED')
        Application.objects.create(user=self.user_a, job=job, status='SUBMITTED')
        Application.objects.create(user=self.user_a, job=job, status='INTERVIEW')
        
        # 1 interview / 3 submissions = 33.3%
        kpis = get_overview_kpis(self.user_a, {})
        self.assertEqual(kpis['applications_submitted'], 3)
        self.assertEqual(kpis['interviews'], 1)
        self.assertEqual(kpis['interview_rate'], 33.3)

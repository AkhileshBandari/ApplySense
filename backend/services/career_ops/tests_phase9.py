import time
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from applysense.middleware import correlation_id_var

User = get_user_model()

class Phase9ImplementationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ops', email='ops@example.com', password='password123')
        self.client = APIClient()

    def test_health_liveness(self):
        url = reverse('health_liveness')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'HEALTHY')
        self.assertIn('timestamp', response.data)

    def test_health_readiness(self):
        url = reverse('health_readiness')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assuming dev DB/Redis are connected
        self.assertIn(response.data['status'], ['HEALTHY', 'DEGRADED']) 

    def test_health_automation(self):
        url = reverse('health_automation')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data['status'], ['HEALTHY', 'DEGRADED', 'UNAVAILABLE'])

    def test_request_correlation_middleware(self):
        url = reverse('health_liveness')
        response = self.client.get(url)
        self.assertIn('X-Request-ID', response.headers)
        
    def test_ssrf_utils_blocking(self):
        from services.career_ops.security_utils import validate_safe_url
        self.assertFalse(validate_safe_url("http://localhost:8080/admin"))
        self.assertFalse(validate_safe_url("http://127.0.0.1/metadata"))
        self.assertFalse(validate_safe_url("http://169.254.169.254/latest/meta-data/"))
        self.assertTrue(validate_safe_url("https://www.google.com"))

    def test_pagination_active(self):
        # Trigger an endpoint that should be paginated now
        self.client.force_authenticate(user=self.user)
        # Using auto apply runs list
        url = reverse('auto_apply_runs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data) # Pagination adds 'results' key
        self.assertIn('count', response.data)

    def test_rate_limiting_active(self):
        # We set anon rate to 100/day. Let's just verify classes exist.
        from django.conf import settings
        self.assertIn('rest_framework.throttling.AnonRateThrottle', settings.REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'])
        

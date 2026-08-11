import os
import sys
import time
import threading
import statistics

# Set up Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "applysense.settings")
os.environ["DJANGO_DEBUG"] = "True"
import django
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

def get_auth_client():
    client = APIClient(SERVER_NAME='localhost')
    user, created = User.objects.get_or_create(username="loadtestuser")
    if created:
        user.set_password("password")
        user.save()
    client.force_authenticate(user=user)
    return client

def test_health_endpoints():
    client = APIClient(SERVER_NAME='localhost')
    endpoints = [
        "/api/health/liveness/",
        "/api/health/readiness/",
    ]
    for ep in endpoints:
        start = time.time()
        res = client.get(ep)
        latency = time.time() - start
        print(f"[HEALTH] {ep} -> {res.status_code} in {latency:.4f}s")

def simulate_load(endpoint, requests_per_thread=20, num_threads=5):
    latencies = []
    status_codes = []
    
    def worker():
        client = get_auth_client()
        for _ in range(requests_per_thread):
            start = time.time()
            try:
                res = client.get(endpoint)
                latencies.append(time.time() - start)
                status_codes.append(res.status_code)
            except Exception as e:
                status_codes.append(500)
    
    threads = []
    start_total = time.time()
    
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    total_time = time.time() - start_total
    
    success = status_codes.count(200) + status_codes.count(201)
    auth_denied = status_codes.count(401) + status_codes.count(403)
    rate_limited = status_codes.count(429)
    errors = len(status_codes) - success - auth_denied - rate_limited
    
    print(f"\n--- Load Test Results for {endpoint} ---")
    print(f"Total Requests: {len(status_codes)}")
    print(f"Concurrency: {num_threads}")
    print(f"Total Time: {total_time:.2f}s")
    if latencies:
        print(f"Average Latency: {statistics.mean(latencies):.4f}s")
        if len(latencies) >= 2:
            print(f"P95 Latency: {statistics.quantiles(latencies, n=100)[94]:.4f}s")
    print(f"Success: {success}")
    print(f"Auth Denied: {auth_denied}")
    print(f"Rate Limited (429): {rate_limited}")
    print(f"Errors (500s/Exceptions): {errors}")

if __name__ == "__main__":
    print("Starting Final ApplySense Load & Health Test via Django Client...")
    test_health_endpoints()
    
    endpoints_to_test = [
        "/api/career-integration/state/os-dashboard/",
        "/api/career-integration/action-center/",
        "/api/career-outcomes/",
        "/api/career-decisions/",
        "/api/career-execution/current/"
    ]
    
    concurrency_levels = [10, 25, 50, 100]
    requests_per_thread = 5 # keep total requests manageable
    
    for endpoint in endpoints_to_test:
        for num_threads in concurrency_levels:
            simulate_load(endpoint, requests_per_thread=requests_per_thread, num_threads=num_threads)

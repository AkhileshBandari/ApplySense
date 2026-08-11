import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'applysense.settings')

app = Celery('applysense')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.task_routes = {
    'automation.tasks.execute_auto_apply_run': {'queue': 'automation'},
}
app.conf.task_soft_time_limit = 1800  # 30 minutes for browser runs
app.conf.task_time_limit = 1860       # 31 minutes hard limit
app.conf.worker_prefetch_multiplier = 1 # Do not prefetch too many heavy tasks

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

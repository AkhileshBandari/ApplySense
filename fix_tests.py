import os, glob

for path in glob.glob('backend/analytics/tests/test_*.py'):
    with open(path, 'r') as f:
        content = f.read()
        
    content = content.replace("username='usera'", "email='usera@example.com'")
    content = content.replace("username='userb'", "email='userb@example.com'")
    content = content.replace('external_id=', 'source_job_id=')
    content = content.replace('source_job_id="1"', 'source_job_id="1", description="test"')
    content = content.replace('source_job_id="2"', 'source_job_id="2", description="test"')
    content = content.replace('source_job_id="3"', 'source_job_id="3", description="test"')
    content = content.replace('source_job_id="4"', 'source_job_id="4", description="test"')
    content = content.replace('source_job_id="5"', 'source_job_id="5", description="test"')
    
    with open(path, 'w') as f:
        f.write(content)

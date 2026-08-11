import os, glob

for path in glob.glob('backend/analytics/tests/test_*.py'):
    with open(path, 'r') as f:
        content = f.read()
        
    content = content.replace("email='usera@example.com'", "username='usera', email='usera@example.com'")
    content = content.replace("email='userb@example.com'", "username='userb', email='userb@example.com'")
    
    with open(path, 'w') as f:
        f.write(content)

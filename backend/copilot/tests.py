from django.test import TestCase
from django.contrib.auth import get_user_model
from copilot.models import ChatThread, ChatMessage

User = get_user_model()

class CopilotModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        
    def test_create_thread(self):
        thread = ChatThread.objects.create(user=self.user, title="Test thread")
        self.assertEqual(thread.user, self.user)
        self.assertEqual(thread.status, 'ACTIVE')
        
    def test_create_message(self):
        thread = ChatThread.objects.create(user=self.user, title="Test thread")
        message = ChatMessage.objects.create(
            thread=thread,
            role='USER',
            content='Hello world'
        )
        self.assertEqual(message.thread, thread)
        self.assertEqual(message.role, 'USER')
        self.assertEqual(thread.messages.count(), 1)

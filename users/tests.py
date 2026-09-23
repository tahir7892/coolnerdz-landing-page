from django.test import TestCase
from django.urls import reverse

from users.models import WaitlistEntry


class HomeViewTests(TestCase):
    def test_home_page_renders(self):
        response = self.client.get(reverse('users:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CoolNerdz')
        self.assertContains(response, 'id="waitlist-form"')


class WaitlistAPITests(TestCase):
    def test_create_requires_email_and_role(self):
        response = self.client.post('/api/waitlist', {}, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'Email and role are required.'})

    def test_create_success(self):
        response = self.client.post(
            '/api/waitlist',
            {'email': 'person@example.com', 'role': 'Student'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.json())
        self.assertTrue(WaitlistEntry.objects.filter(email='person@example.com').exists())

    def test_create_duplicate_email_conflict(self):
        WaitlistEntry.objects.create(email='dup@example.com', role='Teacher')
        response = self.client.post(
            '/api/waitlist',
            {'email': 'dup@example.com', 'role': 'Teacher'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {'error': 'This email is already on the waitlist.'})

    def test_list_entries(self):
        WaitlistEntry.objects.create(email='a@example.com', role='Student')
        WaitlistEntry.objects.create(email='b@example.com', role='Athlete')
        response = self.client.get('/api/waitlist')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['data']), 2)

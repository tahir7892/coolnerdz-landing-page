from smtplib import SMTPException
from unittest import mock

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import WaitlistEntry


# The production .env enables SECURE_SSL_REDIRECT; the test client speaks plain HTTP.
@override_settings(SECURE_SSL_REDIRECT=False)
class HomeViewTests(TestCase):
    def test_home_page_renders(self):
        response = self.client.get(reverse('users:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CoolNerdz')
        self.assertContains(response, 'id="waitlist-form"')


@override_settings(SECURE_SSL_REDIRECT=False)
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


TEST_SMTP_PASSWORD = 'not-a-real-password-7f3a9'


@override_settings(
    SECURE_SSL_REDIRECT=False,
    ADMIN_EMAIL='tahir7892@gmail.com',
    DEFAULT_FROM_EMAIL='CoolNerdz <hello@coolnerdz.com>',
    EMAIL_HOST_PASSWORD=TEST_SMTP_PASSWORD,
    SITE_URL='https://coolnerdz.com',
)
class WaitlistEmailTests(TestCase):
    def post(self, payload):
        return self.client.post('/api/waitlist', payload, content_type='application/json')

    def signup(self, email='new.person@example.com', role='Teacher'):
        return self.post({'email': email, 'role': role})

    def messages_by_recipient(self):
        return {message.to[0]: message for message in mail.outbox}

    def test_successful_signup_sends_subscriber_and_admin_email(self):
        response = self.signup()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {'message': "You're on the waitlist! Check your inbox for a confirmation email."},
        )
        self.assertEqual(WaitlistEntry.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 2)

        messages = self.messages_by_recipient()
        self.assertEqual(set(messages), {'new.person@example.com', 'tahir7892@gmail.com'})
        for message in mail.outbox:
            self.assertEqual(len(message.to), 1)
            self.assertEqual(message.from_email, 'CoolNerdz <hello@coolnerdz.com>')

        subscriber = messages['new.person@example.com']
        self.assertEqual(subscriber.subject, "Welcome to CoolNerdz: you're on the waitlist")
        self.assertIn('new.person@example.com', subscriber.body)
        self.assertIn('Teacher', subscriber.body)
        self.assertIn('https://coolnerdz.com', subscriber.body)
        self.assertNotIn('tahir7892@gmail.com', subscriber.body)

        admin = messages['tahir7892@gmail.com']
        self.assertEqual(admin.subject, 'New CoolNerdz Waitlist Signup: new.person@example.com')
        self.assertEqual(admin.reply_to, ['new.person@example.com'])
        entry = WaitlistEntry.objects.get()
        self.assertIn('new.person@example.com', admin.body)
        self.assertIn('Teacher', admin.body)
        self.assertIn(f'#{entry.pk}', admin.body)
        self.assertIn(entry.created_at.strftime('%B %-d, %Y'), admin.body)
        self.assertIn('welcome confirmation was sent', admin.body)

    def test_emails_are_html_with_plain_text_alternative(self):
        self.signup()

        for message in mail.outbox:
            self.assertTrue(message.body.strip())
            self.assertNotIn('<table', message.body)
            self.assertEqual(len(message.alternatives), 1)
            html, mimetype = message.alternatives[0]
            self.assertEqual(mimetype, 'text/html')
            self.assertIn('<!DOCTYPE html>', html)
            self.assertIn('CoolNerdz', html)
            self.assertIn('new.person@example.com', html)

        html = {m.to[0]: m.alternatives[0][0] for m in mail.outbox}
        self.assertIn("You're on the list.", html['new.person@example.com'])
        self.assertIn('New waitlist signup', html['tahir7892@gmail.com'])

    def test_no_secrets_in_email_content(self):
        self.signup()

        for message in mail.outbox:
            content = message.message().as_string()
            self.assertNotIn(TEST_SMTP_PASSWORD, content)
            self.assertNotIn(settings.SECRET_KEY, content)

    def test_duplicate_signup_sends_no_emails(self):
        WaitlistEntry.objects.create(email='dup@example.com', role='Teacher')

        response = self.signup(email='DUP@example.com')

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {'error': 'This email is already on the waitlist.'})
        self.assertEqual(WaitlistEntry.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_missing_fields_send_no_emails(self):
        for payload in ({}, {'email': 'a@example.com'}, {'role': 'Student'}):
            response = self.post(payload)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), {'error': 'Email and role are required.'})

        self.assertEqual(WaitlistEntry.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_invalid_input_sends_no_emails(self):
        for payload in ({'email': 'not-an-email', 'role': 'Student'}, {'email': 'a@example.com', 'role': 'Wizard'}):
            response = self.post(payload)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {'error': 'An error occurred while saving your submission.'})

        self.assertEqual(WaitlistEntry.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_smtp_failure_keeps_signup_and_returns_success(self):
        with mock.patch.object(EmailMultiAlternatives, 'send', side_effect=SMTPException('boom')), \
                self.assertLogs('users.services.email_service', level='ERROR') as logs:
            response = self.signup()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {'message': "You're on the waitlist! We'll be in touch soon."})
        self.assertTrue(WaitlistEntry.objects.filter(email='new.person@example.com').exists())
        self.assertTrue(any('Subscriber email failed' in line for line in logs.output))
        self.assertTrue(any('Admin notification failed' in line for line in logs.output))
        self.assertNotIn('boom', response.content.decode())

    def test_subscriber_failure_is_flagged_in_admin_email(self):
        real_send = EmailMultiAlternatives.send

        def fail_for_subscriber(message, *args, **kwargs):
            if message.to == ['new.person@example.com']:
                raise SMTPException('recipient refused')
            return real_send(message, *args, **kwargs)

        with mock.patch.object(EmailMultiAlternatives, 'send', fail_for_subscriber), \
                self.assertLogs('users.services.email_service', level='ERROR'):
            response = self.signup()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['tahir7892@gmail.com'])
        self.assertIn('could not be delivered', mail.outbox[0].body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend', EMAIL_HOST='')
    def test_unconfigured_smtp_skips_emails_and_keeps_signup(self):
        with mock.patch('django.core.mail.backends.smtp.EmailBackend.open') as smtp_open, \
                self.assertLogs('users.services.email_service', level='WARNING') as logs:
            response = self.signup()

        smtp_open.assert_not_called()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(WaitlistEntry.objects.count(), 1)
        self.assertIn('EMAIL_HOST is not configured', logs.output[0])

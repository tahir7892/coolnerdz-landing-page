import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string

from users.models import WaitlistEntry

logger = logging.getLogger(__name__)

SMTP_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
SUBSCRIBER_SUBJECT = "Welcome to CoolNerdz: you're on the waitlist"
ADMIN_SUBJECT = 'New CoolNerdz Waitlist Signup'


def _smtp_configured():
    return settings.EMAIL_BACKEND != SMTP_BACKEND or bool(settings.EMAIL_HOST)


def _build_message(subject, template, context, to, reply_to=None):
    text_body = render_to_string(f'emails/{template}.txt', context)
    html_body = render_to_string(f'emails/{template}.html', context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
        reply_to=reply_to,
    )
    message.attach_alternative(html_body, 'text/html')
    return message


def build_subscriber_email(entry, context):
    return _build_message(SUBSCRIBER_SUBJECT, 'waitlist_confirmation', context, [entry.email])


def build_admin_email(entry, context):
    return _build_message(
        f'{ADMIN_SUBJECT}: {entry.email}',
        'waitlist_admin_notification',
        context,
        [settings.ADMIN_EMAIL],
        reply_to=[entry.email],
    )


def _send(message, connection, label, entry):
    message.connection = connection
    try:
        message.send()
    except Exception:
        logger.exception('%s failed for waitlist entry id=%s.', label, entry.pk)
        return False
    logger.info('%s sent for waitlist entry id=%s.', label, entry.pk)
    return True


def send_waitlist_emails(entry):
    """
    Send the subscriber confirmation and the admin notification for a saved
    waitlist entry. Never raises: the signup is already stored, so delivery
    problems are logged and reported back instead of failing the request.

    Returns {'subscriber': bool, 'admin': bool}.
    """
    results = {'subscriber': False, 'admin': False}

    if not _smtp_configured():
        logger.warning('Waitlist emails skipped for entry id=%s: EMAIL_HOST is not configured.', entry.pk)
        return results

    context = {
        'entry': entry,
        'site_url': settings.SITE_URL,
        'site_domain': settings.SITE_URL.split('://', 1)[-1],
        'total_signups': WaitlistEntry.objects.count(),
    }

    connection = get_connection()
    try:
        connection.open()
    except Exception:
        logger.exception('Waitlist emails failed for entry id=%s: could not connect to the SMTP server.', entry.pk)
        return results

    try:
        results['subscriber'] = _send(build_subscriber_email(entry, context), connection, 'Subscriber email', entry)
        # Built after the first send so the admin sees whether the subscriber got their confirmation.
        context['subscriber_emailed'] = results['subscriber']
        results['admin'] = _send(build_admin_email(entry, context), connection, 'Admin notification', entry)
    finally:
        try:
            connection.close()
        except Exception:
            logger.warning('Error closing SMTP connection after waitlist entry id=%s.', entry.pk, exc_info=True)

    return results

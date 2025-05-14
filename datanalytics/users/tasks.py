"""Email sending tasks using Celery and Django's EmailBackend."""

from celery import shared_task
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.conf import settings
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to console
    ]
)

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_email_task(self, subject: str, body: str, from_email: str, recipient_list: list, html_message=None) -> int:
    """Send an email using the SMTP backend.

    :param self: The current task instance.
    :type self: celery.Task
    :param subject: The subject of the email.
    :type subject: str
    :param body: The body of the email.
    :type body: str
    :param from_email: The sender's email address.
    :type from_email: str
    :param recipient_list: List of recipient email addresses.
    :type recipient_list: list
    :param html_message: Optional HTML message to be sent as an alternative.
    :type html_message: str, optional
    :return: The number of successfully sent messages.
    :rtype: int
    """
    try:
        # Create SMTP backend directly
        backend = EmailBackend(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            use_ssl=settings.EMAIL_USE_SSL
        )

        if html_message:
            email = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=from_email,
                to=recipient_list,
                connection=backend
            )
            email.attach_alternative(html_message, "text/html")
        else:
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=from_email,
                to=recipient_list,
                connection=backend
            )
        
        result = email.send(fail_silently=False)
        logger.info(f"Email sent successfully to {recipient_list}")
        return result
        
    except Exception as exc:
        logger.exception(f"Failed to send email to {recipient_list}")
        raise self.retry(exc=exc, countdown=5 * 60)  # Retry after 5 minutes
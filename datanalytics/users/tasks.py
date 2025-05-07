from celery import shared_task
from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_email_task(self, subject, body, from_email, recipient_list, html_message=None):
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
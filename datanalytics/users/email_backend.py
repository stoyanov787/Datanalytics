"""Email authentication backend for Django."""

from django.core.mail.backends.base import BaseEmailBackend
from .tasks import send_email_task
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

class CeleryEmailBackend(BaseEmailBackend):
    """Custom email backend that sends emails using Celery tasks."""
    def send_messages(self, email_messages: list) -> int:
        """Send email messages using Celery tasks.
        
        :param email_messages: List of email messages to be sent.
        :type email_messages: list
        :return: Number of successfully queued messages.
        :rtype: int
        """
        tasks = []
        for msg in email_messages:
            logger.info(f"Queueing email to {msg.to}")
            
            # Check if the message has alternatives and get the HTML content if available
            html_content = None
            if hasattr(msg, "alternatives") and msg.alternatives:
                for content, mimetype in msg.alternatives:
                    if mimetype == 'text/html':
                        html_content = content
                        break
            
            task = send_email_task.delay(
                subject=msg.subject,
                body=msg.body,
                from_email=msg.from_email,
                recipient_list=msg.to,
                html_message=html_content
            )
            tasks.append(task)
            logger.info(f"Email queued with task id: {task.id}")
            
        return len(tasks)  # Return number of queued messages
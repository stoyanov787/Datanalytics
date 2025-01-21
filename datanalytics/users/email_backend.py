from django.core.mail.backends.base import BaseEmailBackend
from .tasks import send_email_task
import logging

logger = logging.getLogger(__name__)

class CeleryEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        tasks = []
        for msg in email_messages:
            logger.info(f"Queueing email to {msg.to}")
            
            html_content = None
            if hasattr(msg, 'alternatives') and msg.alternatives:
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
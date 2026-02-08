from .tasks import send_email_task, send_push_task, send_seller_email_task
from .enqueue import enqueue_order_email, enqueue_push_notification, enqueue_seller_email_task
from django.conf import settings

def queue_email_task(**payload):
    """
    Decide where to send the email task.
    - Local dev → Celery
    - Production → Cloud Tasks
    """
    if getattr(settings, "USE_CLOUD_TASKS", False):
        enqueue_order_email(**payload)
    else:
        send_email_task.delay(**payload)

def queue_push_task(**payload):
    """
    Decide where to send the push notification task.
    - Local dev → Celery
    - Production → Cloud Tasks
    """
    if getattr(settings, "USE_CLOUD_TASKS", False):
        enqueue_push_notification(**payload)
    else:
        send_push_task.delay(**payload)

def queue_seller_email_task(**payload):
    """
    Decide where to send the seller email task.
    - Local dev → Celery
    - Production → Cloud Tasks
    """
    if getattr(settings, "USE_CLOUD_TASKS", False):
        enqueue_seller_email_task(**payload)
    else:
        send_seller_email_task.delay(**payload)
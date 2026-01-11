import logging
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
import json

from order.models import Order, OrderEmailLog, PushSubscription
from pywebpush import webpush, WebPushException

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_email_task(self, *, email_log_id, to_email, subject, template, context):
    logger.warning("Sending email for log %s", email_log_id)

    email_log = OrderEmailLog.objects.select_related("order").get(id=email_log_id)

    """ if email_log.status == "sent":
        return """

    try:
        order = Order.objects.get(id=context["order_id"])

        user = None
        if context.get("user_id"):
            user = User.objects.get(id=context["user_id"])

        email_context = {
            "order": order,
            "user": user,
            "cta_url": context["cta_url"],
            "site_url": settings.SITE_URL,
            "event": context["event"],
        }

        logger.info("Sending email to %s with context %s", to_email, email_context)

        html_content = render_to_string(template, email_context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_content, "text/html")

        sent = msg.send()
        logger.info("Email sent count=%s", sent)

        email_log.mark_sent()
        email_log.sent_at = timezone.now()
        email_log.save(update_fields=["status", "sent_at"])

    except Exception as exc:
        logger.exception("Email sending failed")
        email_log.mark_failed()
        email_log.save(update_fields=["status"])
        raise self.retry(exc=exc, countdown=30)

@shared_task(bind=True, max_retries=3)
def send_push_task(self, *, user_id, payload):
    """
    Sends a web push notification to all subscriptions for a given user.
    
    payload = {
        "title": "Order Paid ✅",
        "body": "Your order #1234 has been confirmed",
        "url": "/order/my-orders/"
    }
    """
    subscriptions = PushSubscription.objects.filter(user_id=user_id)

    if not subscriptions.exists():
        logger.info("No push subscriptions found for user %s", user_id)
        return
    
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth
                    }
                },
                data=json.dumps(payload),
                vapid_private_key=settings.WEBPUSH_PRIVATE_KEY,
                vapid_claims={
                    "sub": f"mailto:{settings.DEFAULT_FROM_EMAIL}"
                }
            )

            logger.info("Push sent to %s (%s)", user_id, sub.device_name or "unknown device")
            sub.touch()

        except WebPushException as exc:
            logger.warning("Push failed for subscription %s: %s", sub.endpoint, exc)
            # Optional: delete invalid subscriptions
            if exc.response and exc.response.status_code == 410:
                sub.delete()
                logger.info("Deleted expired subscription %s", sub.endpoint)
            
            # Retry
            raise self.retry(exc=exc, countdown=30)
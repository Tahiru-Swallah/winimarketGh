import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
import json

from order.models import Order, OrderEmailLog, PushSubscription
from pywebpush import webpush, WebPushException

from celery.utils.log import get_task_logger

logger = logging.getLogger(__name__)

User = get_user_model()

try:
    from celery import shared_task
except ImportError:
    shared_task = None  # Celery not installed or not used in prod

def _send_email_task(*, email_log_id, to_email, subject, template, context):
    logger.warning("Sending email for log %s", email_log_id)

    logger.info(f"📧 email_log_id: {email_log_id}")
    logger.info(f"🔹 Subject: {subject}")
    logger.info(f"🔹 To email: {to_email}")
    logger.info(f"🔹 template: {template}")
    logger.info(f"🔹 context: {context}")

    email_log = OrderEmailLog.objects.select_related("order").get(id=email_log_id)

    if email_log.status == "sent":
        return

    order = ( Order.objects.select_related("buyer", "buyer__user").prefetch_related("items", "items__product", "items__product__images",).get(id=context["order_id"]))

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

    logger.info("🧩 Rendered HTML length: %s", len(html_content))

    msg = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        sent = msg.send(fail_silently=False)
        logger.info("Email sent count=%s", sent)
        email_log.mark_sent()
        email_log.save(update_fields=["status", "sent_at"])

    except Exception as e:
        logger.exception(f"❌ Email sending failed: {e}")
        email_log.mark_failed()
        email_log.save(update_fields=["status"])
        return
    
if shared_task:
    @shared_task(bind=True, max_retries=3)
    def send_email_task(self, **kwargs):
        try:
            return _send_email_task(**kwargs)
        except Exception as exc:
            logger.exception("Email failed")
            raise self.retry(exc=exc, countdown=30)
else:
    def send_email_task(**kwargs):
        return _send_email_task(**kwargs)


def _send_push_task(*, user_id, payload):
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
            status_code = getattr(exc.response, "status_code", None)
            logger.warning("Push failed for subscription %s (status: %s): %s", sub.endpoint, status_code, exc)

            # Delete expired/invalid subscriptions (410 Gone or 400 Bad Request)
            if status_code in [400, 410]:
                sub.delete()
                logger.info("Deleted invalid/expired subscription %s", sub.endpoint)
                continue  # Continue to other subscriptions

if shared_task:
    @shared_task(bind=True, max_retries=3)
    def send_push_task(self, **kwargs):
        try:
            return _send_push_task(**kwargs)
        except Exception as exc:
            logger.exception("Push notification failed")
            raise self.retry(exc=exc, countdown=30)
else:
    def send_push_task(**kwargs):
        return _send_push_task(**kwargs)


def _send_seller_email_task(*, notification_log_id, to_email, subject, template, context):
    logger.warning("Sending seller email for log %s", notification_log_id)

    from registration.models import SellerNotificationLog, SellerProfile

    log = SellerNotificationLog.objects.select_related(
        "seller", "user"
    ).get(id=notification_log_id)

    if log.status == "sent":
        return


    seller = SellerProfile.objects.get(id=context["seller_id"])
    user = None

    if context.get("user_id"):
        user = User.objects.get(id=context["user_id"])

    email_context = {
        "seller": seller,
        "user": user,
        "cta_url": context["cta_url"],
        "site_url": settings.SITE_URL,
        "event": context["event"],
    }

    html_content = render_to_string(template, email_context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send()
        logger.info("Seller email sent to %s", to_email)
        log.mark_sent()
    except Exception as e:
        logger.exception("❌ Seller email sending failed: %s", e)
        log.mark_failed()
        raise

if shared_task:
    @shared_task(bind=True, max_retries=3)
    def send_seller_email_task(self, **kwargs):
        try:
            return _send_seller_email_task(**kwargs)
        except Exception as exc:
            logger.exception("Seller email failed: %s", exc)
            raise self.retry(exc=exc, countdown=30)
else:
    def send_seller_email_task(**kwargs):
        return _send_seller_email_task(**kwargs)
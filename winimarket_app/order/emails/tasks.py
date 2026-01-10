import logging
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

from order.models import Order, OrderEmailLog

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

from .routings import ORDER_EMAIL_ROUTING, ORDER_PUSH_ROUTING
from .recipients import resolve_recipient
from .tasks import send_email_task, send_push_task
from order.constants.email_event import OrderEmailEvent
from order.models import OrderEmailLog
from django.conf import settings

class OrderEmailDispatcher:

    @staticmethod
    def dispatcher(order, event: str):
        """
        Dispatch emails for a given order event.
        """

        routes = ORDER_EMAIL_ROUTING.get(event)

        if not routes:
            return
        
        for role, config in routes.items():
            recipients = resolve_recipient(order, role)

            for recipient in recipients:
                OrderEmailDispatcher._send_email(
                    order=order,
                    event=event,
                    role=role,
                    recipient=recipient,
                    config=config
                )

                OrderEmailDispatcher._send_push(
                    order=order,
                    event=event,
                    role=role,
                    recipient=recipient
                )

    @staticmethod
    def _send_email(*, order, event, role, recipient, config):
        """
        Create OrderEmailLog and enqueue Celery task
        """

        if OrderEmailLog.objects.filter(event=event, order=order, recipient_email=recipient['email'], status="sent").exists():
            return
        
        email_log = OrderEmailLog.objects.create(
            order=order,
            event=event,
            recipient_role=role,
            recipient_email=recipient["email"],
            subject=config["subject"],
        )

        context = {
            "order_id": order.id,
            "user_id": recipient.get("user_id"),
            "cta_url": config["cta"].format(order_id=order.id),
            "site_url": settings.SITE_URL,
            "event": event,
        }

        send_email_task.delay(
            email_log_id=email_log.id,
            to_email=recipient["email"],
            subject=config["subject"],
            template=config["template"],
            context=context
        )

    @staticmethod
    def _send_push(*, order, event, role, recipient):
        routes = ORDER_PUSH_ROUTING.get(event)

        if not routes:
            return
        
        config = routes.get(role)
        if not config:
            return
        
        user_id = recipient.get("user_id")
        if not user_id:
            return
        
        payload = {
            "title": config["title"],
            "body": config["body"],
            "url": config["url"],
            "order_id": str(order.id),
        }

        send_push_task.delay(
            user_id=user_id,
            payload=payload
        )
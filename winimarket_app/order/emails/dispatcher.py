from .routings import ORDER_EMAIL_ROUTING
from .recipients import resolve_recipient
from .tasks import send_email_task
from order.constants.email_event import OrderEmailEvent
from order.models import OrderEmailLog

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
            "event": event,
        }

        send_email_task.delay(
            email_log_id=email_log.id,
            to_email=recipient["email"],
            subject=config["subject"],
            template=config["template"],
            context=context
        )

        email_log.mark_sent()
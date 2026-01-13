from .routings import ORDER_EMAIL_ROUTING, ORDER_PUSH_ROUTING, SELLER_NOTIFICATION_ROUTING
from .recipients import resolve_recipient
from .tasks import send_email_task, send_push_task, send_seller_email_task
from order.models import OrderEmailLog
from django.conf import settings
from registration.models import SellerNotificationLog, SellerProfile
from django.contrib.auth import get_user_model

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

User = get_user_model()
class SellerNotificationDispatcher:

    @staticmethod
    def dispatch(*, seller_id, event):
        """
        Dispatch email + push notifications to a seller for a given event
        """

        routes = SELLER_NOTIFICATION_ROUTING.get(event)

        if not routes:
            return
        
        seller = SellerProfile.objects.get(id=seller_id)
        user = seller.profile.user

        if not user:
            return
    
        email_cfg = routes.get('email')
        print(f"Printing User: {email_cfg}")
        if email_cfg:
            log = SellerNotificationLog.objects.create(
                seller=seller,
                user=user,
                event=event,
                channel='email',
                subject=email_cfg['subject']
            )

            context = {
                "seller_id": seller.id,
                "user_id": user.id,
                "event": event,
                "cta_url": email_cfg["cta"],
                "site_url": settings.SITE_URL,
            }

            send_seller_email_task.delay(
                notification_log_id=log.id,
                to_email=user.email,
                subject=email_cfg["subject"],
                template=email_cfg["template"],
                context=context
            )

        push_cfg = routes.get('push')
        if push_cfg:
            log = SellerNotificationLog.objects.create(
                seller=seller,
                user=user,
                event=event,
                channel='push',
                payload=push_cfg
            )

            send_push_task.delay(
                user_id=user.id,
                payload=push_cfg
            )

            log.mark_sent()
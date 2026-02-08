from .routings import ORDER_EMAIL_ROUTING, ORDER_PUSH_ROUTING, SELLER_NOTIFICATION_ROUTING
from .recipients import resolve_recipient
from .tasks import send_push_task, send_seller_email_task
from order.models import OrderEmailLog
from django.conf import settings
from registration.models import SellerNotificationLog, SellerProfile
from django.contrib.auth import get_user_model
from .utils import queue_email_task, queue_push_task, queue_seller_email_task
from django.db import transaction

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
                transaction.on_commit (
                    lambda order=order, event=event, role=role, recipient=recipient, config=config: OrderEmailDispatcher._send_email(order=order, event=event, role=role, recipient=recipient, config=config)
                )

                transaction.on_commit (
                    lambda order=order, event=event, role=role, recipient=recipient: OrderEmailDispatcher._send_push(order=order, event=event, role=role, recipient=recipient)
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

        user_id = recipient.get("user_id")

        if not user_id:
            return 

        context = {
            "order_id": str(order.id),
            "user_id": str(user_id),
            "cta_url": config["cta"].format(order_id=order.id),
            "site_url": settings.SITE_URL,
            "event": event,
        }

        payload = {
            "email_log_id": str(email_log.id),
            "to_email": recipient["email"],
            "subject": config["subject"],
            "template": config["template"],
            "context": context
        }

        queue_email_task(**payload)

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
            "user_id": str(user_id),
            "payload":{
                "title": config["title"],
                "body": config["body"],
                "url": config["url"],
                "order_id": str(order.id),
            }
        }

        queue_push_task(**payload)

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
                "seller_id": str(seller.id),
                "user_id": str(user.id),
                "event": event,
                "cta_url": email_cfg["cta"],
                "site_url": settings.SITE_URL,
            }

            payload = {
                "notification_log_id": str(log.id),
                "to_email": user.email,
                "subject": email_cfg["subject"],
                "template": email_cfg["template"],
                "context": context
            }

            queue_seller_email_task(**payload)

        push_cfg = routes.get('push')
        if push_cfg:
            log = SellerNotificationLog.objects.create(
                seller=seller,
                user=user,
                event=event,
                channel='push',
                payload=push_cfg
            )

            payload = {
                "user_id": str(user.id),
                "payload": push_cfg
            }

            queue_push_task(**payload)

            log.mark_sent()
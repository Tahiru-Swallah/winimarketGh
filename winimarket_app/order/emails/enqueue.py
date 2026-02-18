import logging
import json
from decimal import Decimal
from google.cloud import tasks_v2
from django.conf import settings
from google.api_core.exceptions import AlreadyExists
import json
import uuid
from datetime import datetime, date

logger = logging.getLogger(__name__)


def safe_json_dumps(data):
    
    def default(o):
        if isinstance(o, uuid.UUID):
            return str(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        raise TypeError(f"Object of type {type(o)} is not JSON serializable.")   # final fallback

    return json.dumps(data, default=default)

def enqueue_order_email(**payload):
    client = tasks_v2.CloudTasksClient()

    parent = client.queue_path(
        settings.GCP_PROJECT_ID,
        settings.GCP_REGION,
        settings.CLOUD_TASKS_QUEUE_NAME
    )

    body = safe_json_dumps({
        "task": "send_email_task",
        "payload": payload
    }).encode()

    task_id = f"order-email-{payload.get('email_log_id')}"

    task = {
        "name": client.task_path(
            settings.GCP_PROJECT_ID,
            settings.GCP_REGION,
            settings.CLOUD_TASKS_QUEUE_NAME,
            task_id
        ),

        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": settings.CLOUD_TASKS_HANDLER_URL,
            "headers": {"Content-Type": "application/json"},
            "body": body,
            "oidc_token": {
                "service_account_email": settings.CLOUD_TASKS_SERVICE_ACCOUNT,
                "audience": settings.CLOUD_TASKS_AUDIENCE,
            },
        }
    }

    try:
        response = client.create_task(request={"parent": parent, "task": task})
        logger.info("✅ Cloud Task created: %s", response.name)
        return response
    except AlreadyExists:
        logger.warning("⚠️ Task already exists, skipping duplicate enqueue.")
    except Exception as e:
        logger.exception("❌ Failed to enqueue Cloud Task: %s", e)
        raise

def enqueue_push_notification(**payload):
    client = tasks_v2.CloudTasksClient()

    parent = client.queue_path(
        settings.GCP_PROJECT_ID,
        settings.GCP_REGION,
        settings.CLOUD_TASKS_QUEUE_NAME
    )

    body = safe_json_dumps({
        "task": "send_push_task",
        "payload": payload
    }).encode()
    
    task_id = f"order-push-{payload.get('user_id')}-{uuid.uuid4()}"

    task = {
        "name": client.task_path(
            settings.GCP_PROJECT_ID,
            settings.GCP_REGION,
            settings.CLOUD_TASKS_QUEUE_NAME,
            task_id
        ),
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": settings.CLOUD_TASKS_HANDLER_URL,
            "headers": {"Content-Type": "application/json"},
            "body": body,
            "oidc_token": {
                "service_account_email": settings.CLOUD_TASKS_SERVICE_ACCOUNT,
                "audience": settings.CLOUD_TASKS_AUDIENCE,
            },
        }
    }

    try:
        response = client.create_task(request={"parent": parent, "task": task})
        logger.info("✅ Push Cloud Task created: %s", response.name)
        return response
    except AlreadyExists:
        logger.warning("⚠️ Push task already exists, skipping duplicate enqueue.")
    except Exception as e:
        logger.exception("❌ Failed to enqueue push Cloud Task: %s", e)
        raise

def enqueue_seller_email_task(**payload):
    client = tasks_v2.CloudTasksClient()

    parent = client.queue_path(
        settings.GCP_PROJECT_ID,
        settings.GCP_REGION,
        settings.CLOUD_TASKS_QUEUE_NAME
    )

    body = safe_json_dumps({
        "task": "send_seller_email_task",
        "payload": payload
    }).encode()

    task_id = f"seller-email-{payload.get('notification_log_id')}"

    task = {
        "name": client.task_path(
            settings.GCP_PROJECT_ID,
            settings.GCP_REGION,
            settings.CLOUD_TASKS_QUEUE_NAME,
            task_id
        ),
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": settings.CLOUD_TASKS_HANDLER_URL,
            "headers": {"Content-Type": "application/json"},
            "body": body,
            "oidc_token": {
                "service_account_email": settings.CLOUD_TASKS_SERVICE_ACCOUNT,
                "audience": settings.CLOUD_TASKS_AUDIENCE,
            },
        }
    }

    try:
        response = client.create_task(request={"parent": parent, "task": task})
        logger.info("✅ Seller Email Cloud Task created: %s", response.name)
        return response
    except AlreadyExists:
        logger.warning("⚠️ Seller email task already exists, skipping duplicate enqueue.")
    except Exception as e:
        logger.exception("❌ Failed to enqueue seller email Cloud Task: %s", e)
        raise
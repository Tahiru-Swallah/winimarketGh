import json
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings

from .tasks import (
    _send_email_task,
    _send_seller_email_task,
    _send_push_task,
)


@csrf_exempt
def cloud_task_handler(request):
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("🔥 CloudTask handler triggered")

    if request.method != "POST":
        logger.warning("Invalid request method: %s", request.method)
        return HttpResponseBadRequest("Invalid request method")

    # ------------------------------------------------------------------
    # 1️⃣ Verify OIDC token
    # ------------------------------------------------------------------
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Missing Authorization header")
        return HttpResponseForbidden("Missing Authorization header")

    token = auth_header.split("Bearer ")[1]

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            audience=settings.CLOUD_TASKS_AUDIENCE,
        )

        expected_sa = settings.CLOUD_TASKS_SERVICE_ACCOUNT
        if idinfo.get("email") != expected_sa:
            logger.warning("Invalid service account: %s", idinfo.get("email"))
            return HttpResponseForbidden("Invalid service account")

    except Exception as e:
        return HttpResponseForbidden(f"Token verification failed: {e}")

    # ------------------------------------------------------------------
    # 2️⃣ Parse payload
    # ------------------------------------------------------------------
    try:
        data = json.loads(request.body or "{}")
        logger.info("📦 Payload: %s", data)

        task = data.get("task")
        payload = data.get("payload")

        if not task or payload is None:
            return HttpResponseBadRequest("Missing task or payload")

    except Exception as e:
        return HttpResponseBadRequest(f"Invalid JSON payload: {e}")

    # ------------------------------------------------------------------
    # 3️⃣ Route task
    # ------------------------------------------------------------------
    try:
        if task == "send_email_task":
            logger.info("Executing email tasks")

            try:
                _send_email_task(**payload)
            except Exception as e:
                logger.exception("Email task failed: %s", e)
                raise

        elif task == "send_seller_email_task":
            logger.info("Executing seller email")
            try:
                _send_seller_email_task(**payload)
            except Exception as e:
                logger.exception("Seller email task failed: %s", e)
                raise

        elif task == "send_push_task":
            logger.info("Executing push task for user_id=%s", payload.get("user_id"))

            try:
                _send_push_task(**payload)
            except Exception as e:
                logger.exception("Push task failed: %s", e)
                raise
        else:
            return HttpResponseBadRequest(f"Unknown task: {task}")

        logger.info("✅ Task executed: %s", task)
        return JsonResponse({"status": "success"})

    except Exception as e:
        logger.exception("❌ Task execution failed: %s", e)
        return JsonResponse(
            {"status": "error", "detail": str(e)},
            status=500
        )

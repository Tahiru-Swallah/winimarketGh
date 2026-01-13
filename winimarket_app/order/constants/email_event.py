class OrderEmailEvent:
    """
    Canonical order email events.
    Used across Celery tasks, signals, and email templates.
    """

    # ORDER CREATION
    ORDER_CREATED = "order_created"

    # PAYMENT
    ORDER_PAID = "order_paid"
    PAYMENT_FAILED = "payment_failed"

    # FULFILLMENT
    ORDER_ACCEPTED = "order_accepted"
    ORDER_REJECTED = "order_rejected"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"

    # COMPLETION
    ORDER_COMPLETED = "order_completed"

    # CANCELLATION & REFUNDS
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REFUNDED = "order_refunded"

class SellerNotificationEvent:
    """
    Canonical seller notification events.
    Used for email + push notifications related to seller lifecycle.
    """

    # VERIFICATION
    SELLER_VERIFIED = "seller_verified"
    SELLER_VERIFICATION_REJECTED = "seller_verification_rejected"

    # (Future-ready)
    SELLER_SUSPENDED = "seller_suspended"
    SELLER_REACTIVATED = "seller_reactivated"
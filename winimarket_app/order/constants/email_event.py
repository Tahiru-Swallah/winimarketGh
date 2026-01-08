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

from order.constants.email_event import OrderEmailEvent, SellerNotificationEvent

ORDER_EMAIL_ROUTING = {
    OrderEmailEvent.ORDER_PAID: {
        "buyer": {
            "template": "emails/buyer/order_paid.html",
            "cta": "/order/my-orders/",
            "subject": "Your Order has been placed and Payment confirmed"
        },
        "seller": {
            "template": "emails/seller/order_paid.html",
            "cta": "/account/seller/dashboard/",
            "subject": "New Order received and Order has been paid – prepare for delivery"
        }
    },

    OrderEmailEvent.ORDER_DELIVERED: {
        "buyer": {
            "template": "emails/buyer/order_delivered.html",
            "cta": "/order/my-orders/",
            "subject": "Your order is marked delivered and is on the way 🚚"
        }
    },

    OrderEmailEvent.ORDER_COMPLETED: {
        "buyer": {
            "template": "emails/buyer/order_completed.html",
            "cta": "/order/my-orders/",
            "subject": "Order completed 🎉"
        },
        "seller": {
            "template": "emails/seller/order_completed.html",
            "cta": "/account/seller/dashboard/",
            "subject": "Order completed successfully"
        }
    },
}

ORDER_PUSH_ROUTING = {
    OrderEmailEvent.ORDER_PAID: {
        "buyer": {
            "title": "Order confirmed ✅",
            "body": "Your payment was successful",
            "url": "/order/my-orders/"
        },
        "seller": {
            "title": "New order received 🛒",
            "body": "An order has been paid and is ready",
            "url": "/account/seller/dashboard/"
        }
    },

    OrderEmailEvent.ORDER_DELIVERED: {
        "buyer": {
            "title": "Order delivered 🚚",
            "body": "Your order has been delivered",
            "url": "/order/my-orders/"
        }
    },

    OrderEmailEvent.ORDER_COMPLETED: {
        "buyer": {
            "title": "Order completed 🎉",
            "body": "Thanks for shopping on Winimarket",
            "url": "/order/my-orders/"
        },
        "seller": {
            "title": "Order completed",
            "body": "An order has been completed successfully",
            "url": "/account/seller/dashboard/"
        }
    }
}

SELLER_NOTIFICATION_ROUTING = {
    SellerNotificationEvent.SELLER_VERIFIED: {
        "email": {
            "template": "emails/seller/seller_verified.html",
            "subject": "Your seller account has been verified 🎉",
            "cta": "/account/seller/dashboard/",
        },
        "push": {
            "title": "You’re verified! 🎉",
            "body": "Your seller account is approved. You can now start selling on Winimarket.",
            "url": "/account/seller/dashboard/",
        },
    },

    SellerNotificationEvent.SELLER_VERIFICATION_REJECTED: {
        "email": {
            "template": "emails/seller/seller_verification_rejected.html",
            "subject": "Seller verification update",
            "cta": "/account/seller/dashboard/",
        },
        "push": {
            "title": "Verification update",
            "body": "Your seller verification was not approved. Please review and resubmit.",
            "url": "/account/seller/dashboard/",
        },
    },
}

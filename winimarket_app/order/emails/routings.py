from order.constants.email_event import OrderEmailEvent

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
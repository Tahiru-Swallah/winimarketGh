from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    # API FOR ORDERS
    path('api/order/', views.create_order),
    path('api/get/order/', views.list_orders),
    path('api/order/detail/<uuid:order_id>/', views.order_detail),

    #CANCEL ORDER
    path('cancel/order/<uuid:order_id>/', views.cancel_order, name='cancel_order'),

    #PAYMENT VERIFICATION
    path('initialize-payment/<uuid:order_id>/', views.initialize_payment, name='initialize_payment'),
    path('verify-payment/<uuid:order_id>/', views.verify_payment, name='verify_payment'),
    path('paystack-webhook/', views.paystack_webhook, name='paystack_webhook'),

    #TEMPLATE VIEWS FOR ORDER
    path('', views.order_template_view, name='order_create'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('verify_payment/<uuid:order_id>/page/', views.verify_payment_page, name='verify_payment_page'),
]
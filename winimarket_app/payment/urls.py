from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    # API FOR PAYMENTS
    path('initialize-payment/<uuid:order_id>/', views.initialize_payment, name='initialize_payment'),
    path('verify-payment/<uuid:order_id>/', views.verify_payment, name='verify_payment'),
    path('paystack-webhook/', views.paystack_webhook, name='paystack_webhook'),
]
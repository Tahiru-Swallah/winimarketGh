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
    path('direct/purchase/', views.direct_purchase, name='direct_purchase'),

    #TEMPLATE VIEWS FOR ORDER
    path('', views.order_template_view, name='order_create'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('verify_payment/<uuid:order_id>/page/', views.verify_payment_page, name='verify_payment_page'),
]
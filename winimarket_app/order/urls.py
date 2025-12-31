from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    path('api/checkout/', views.checkout, name='checkout'),
    path('api/detail/<uuid:order_id>/', views.order_detail),
    path('api/orders/buyer/', views.my_orders, name='buyer-order'),
    path('api/orders/seller/', views.seller_orders, name='seller-orders'),

    path('api/orders/<uuid:order_id>/update/', views.update_order_status, name='order-update'),
    path('api/confirm/<uuid:order_id>/order/', views.confirm_delivery, name='confirm-order'),

    path('api/shipping_addresses/create/', views.create_shipping_address, name='create-shipping-address'),
    path('api/shipping_addresses/', views.list_shipping_addresses, name='list-shipping-addresses'),

    path('checkout/', views.checkout_page, name='checkout-page'),
    path('my-orders/', views.orders_page, name='orders-page'),
    path('detail/<uuid:order_id>/', views.order_detail_page, name='order-detail'),
    path('payment/verify/', views.payment_verify_template, name='verify-payment'),
]
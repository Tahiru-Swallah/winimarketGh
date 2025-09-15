from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    #API endpoints for cart operations
    path('api/view/', views.view_cart),
    path('api/add/', views.add_to_cart),
    path('api/remove/<uuid:product_id>/', views.remove_from_cart),
    path('api/update/<uuid:product_id>/', views.update_cart_item),
]
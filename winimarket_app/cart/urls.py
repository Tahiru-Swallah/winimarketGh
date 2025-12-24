from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    #API endpoints for cart operations
    path('api/view/', views.view_cart),
    path('api/add/', views.add_to_cart),
    path('api/remove/<uuid:cart_item_id>/', views.remove_from_cart),
    path('api/update/<uuid:cart_item_id>/', views.update_cart_item),
]
from django.urls import path
from . import views 

app_name = 'products'

urlpatterns = [
    # Category API URLs
    path('api/categories/', views.category_list_create),

    # Product API URLs
    path('api/products/', views.product_list_create),
    path('api/products/<uuid:pk>/', views.product_detail_update_delete),

    # WishList API URLs
    path('api/wishlist/<uuid:product_id>/', views.wishlist_view),
    path('api/wishlist/', views.wishlist_view),

    #TEMPLATE RENDERING
    path('', views.product_list_view, name='product_list'),
    path('wishlist/', views.wishlist_template_view, name='wishlist_template'),
]
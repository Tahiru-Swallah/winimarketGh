from django.urls import path
from . import views 
from django.views.generic import TemplateView

app_name = 'products'

urlpatterns = [
    # Category API URLs
    path('products/api/categories/', views.category_list_create),

    # Product API URLs
    path('products/api/products/', views.product_list_create),
    path('products/api/products/<uuid:pk>/', views.product_detail_update_delete),
    path('product/api/search/', views.search_products),
    path('product/api/search/suggestions/', views.search_suggestions),

    # WishList API URLs
    path('products/api/wishlist/<uuid:product_id>/', views.wishlist_view),
    path('products/api/wishlist/', views.wishlist_view),

    #TEMPLATE RENDERING
    path('', views.product_list_view, name='product_list'),
    path('products/wishlist/', views.wishlist_template_view, name='wishlist_template'),

    path('products/<uuid:product_id>/', TemplateView.as_view(template_name="products/product_list.html")),
]
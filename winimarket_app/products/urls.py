from django.urls import path
from . import views 
from django.views.generic import TemplateView

app_name = 'products'

urlpatterns = [
    # Category API URLs
    path('products/api/categories/', views.category_list_create),

    # Product API URLs
    path('products/api/products/', views.product_list_create),
    path('products/api/products/<uuid:pk>/', views.product_detail),
    path('product/api/search/', views.search_products),
    path('product/api/search/suggestions/', views.search_suggestions),

    path('product/detail/<uuid:pk>/<slug:slug>/', views.product_detail_view, name='product_detail_api'),

    #TEMPLATE RENDERING
    path('', views.product_list_view, name='product_list'),

    # Seller's VIEW APIs
    path('api/seller/products/', views.seller_products),
    path('api/seller/product/<uuid:product_id>/update/', views.seller_update_product),
    path('api/seller/product/<uuid:product_id>/delete/', views.seller_delete_product),
]
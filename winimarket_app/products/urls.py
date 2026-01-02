from django.urls import path
from . import views 
from django.views.generic import TemplateView

app_name = 'products'

urlpatterns = [
    # Category API URLs
    path('products/api/categories/', views.category_list_create),

    # Product API URLs
    path('products/api/products/', views.product_list_create),
    path('products/api/products/<uuid:pk>/', views.product_detail, name="product_detai_api"),
    path('product/api/search/', views.search_products),
    path('product/api/search/suggestions/', views.search_suggestions),

    path('product/detail/<uuid:pk>/<slug:slug>/', views.product_detail_view, name='product_detail'),

    #TEMPLATE RENDERING
    path('', views.product_list_view, name='product_list'),
    path('product/upload/', views.product_upload_view, name='product_upload'),
    path('product/seller/edit/', views.product_upload_view, name='product_upload'),

    # Seller's VIEW APIs
    path('api/seller/dashboard/stats/', views.seller_dashboard_stats),
    path('api/seller/products/', views.seller_products),
    path('api/seller/product/update/<uuid:product_id>/', views.seller_update_product),
    path('api/seller/product/delete/<uuid:product_id>/', views.seller_delete_product),
]
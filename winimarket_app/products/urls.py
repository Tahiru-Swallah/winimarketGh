from django.urls import path
from . import views 
from django.views.generic import TemplateView
from order.emails.view_cloudtask import cloud_task_handler

from django.contrib.sitemaps.views import sitemap
from .sitemap import ProductSiteMap

app_name = 'products'

sitemaps = {
    'products': ProductSiteMap,
}

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

    path('offline/', views.offline_view, name='offline'),
    path('support/', views.support_view, name='support'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.policy_view, name='policy'),

    path(
        "service-worker.js",
        TemplateView.as_view(
            template_name="service-worker.js",
            content_type="text/javascript",
        ),
    ),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),

    path("tasks/handler/", cloud_task_handler, name="cloud_task_handler"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),

    path('api/product/<uuid:product_id>/reviews/', views.product_reviews, name='product_reviews'),
    path('api/product/reviews/add/', views.create_review, name='add_product_review'),
    path('api/product/contact_click/', views.track_contact_click, name='track_contact_click'),
]
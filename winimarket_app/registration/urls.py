from django.urls import path
from .views import CustomTokenObtainPairView, registration, logOutView
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'registration'

urlpatterns = [
    #HOME PAGE
    path('', views.home, name='home'),

    #LOGIN APIs URLs
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    #REGISTER APIs URL
    path('api/register/', registration, name='register'),

    #LOGOUT API
    path('api/logout/', logOutView.as_view(), name='logout'),

    #LOGIN VIEWS
    path('login/', views.login_view, name='login'),

    # CHANGE PASSWORD API
    path('api/change-password/', views.ChangePasswordView.as_view()),

    #PROFILE API
    path('api/profile/', views.profile_view),
    
    #ROLE SELECTION API
    path('api/profile/set-role/', views.profile_view),

    #SELLER PROFILE API
    path('api/seller-profile/', views.seller_profile_view),
]

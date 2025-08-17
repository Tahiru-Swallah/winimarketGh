from django.urls import path
from .views import CustomTokenObtainPairView, registration, logout
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
    path('api/logout/', logout, name='logout'),
]

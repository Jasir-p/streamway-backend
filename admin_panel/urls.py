from django.urls import path
from .views import admin_login,admin_dashboard,admin_analytics,logout_admin,get_active_logs
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,

)

urlpatterns = [
    path('admin-login/', admin_login, name='admin-login'),
    path('admin-dashboard/', admin_dashboard, name='admin-dashboard'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin-analytic/', admin_analytics, name='admin-analytic'),
    path('logout-admin/', logout_admin, name='logout-admin'),
    path('get-active-logs/', get_active_logs, name='get-active-logs'),

]

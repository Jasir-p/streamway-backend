from django.urls import path
from .views import admin_login,admin_dashboard

urlpatterns = [
    path('admin-login/', admin_login, name='admin-login'),
    path('admin-dashboard/', admin_dashboard, name='admin-dashboard'),
]

from django.urls import path
from .views import tenant_dashboard_content


urlpatterns = [
     path('tenant_dashboard_content/', tenant_dashboard_content, name='tenant_dashboard_content'),
]

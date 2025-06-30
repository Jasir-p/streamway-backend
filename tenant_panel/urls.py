from django.urls import path
from .views import tenant_dashboard_content,get_employee_analytics,get_team_analytics,get_tenant_analytics


urlpatterns = [
     path('tenant_dashboard_content/', tenant_dashboard_content, name='tenant_dashboard_content'),
     path('get-employee-analytics/', get_employee_analytics, name='get-employee-analytics'),
     path('get-team-analytics/', get_team_analytics, name='get-team-analytics'),
     path('get-tenant-analytics/', get_tenant_analytics, name='get-tenant-analytics'),
     
]

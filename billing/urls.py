from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import webhook_handler

router = DefaultRouter()
router.register(r'tenant/billing', views.TenantBillingViewSet, basename='tenant-billing')
router.register(r'tenant/invoices', views.InvoiceViewSet, basename='tenant-invoices'),
router.register(r'admin/billings', views.TenantBillingViewSet, basename='admin-billing')


urlpatterns = [

    path('api/', include(router.urls)),
    path('api/tenant/invoice-status',views.get_invoice_status,name='tenant-invoice-status'),
    path('api/tenants/all-bill', views.get_all_tenant_bill,name='tenants-all-bill'),
    

    
]
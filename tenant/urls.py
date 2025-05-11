from django.urls import path
from tenant.views import TenantView, RegisterTenant, SendOTPView, LoginView, CheckAuthView, MyTokenRefreshView,resend_otp_view,logout_user,CompanydetailView,handle_active
from django.contrib import admin
from billing import webhook_handler

urlpatterns = [
     path('api/', CheckAuthView.as_view()),
     path('action/', TenantView.as_view(), name='tenant-list'),
     path('admin/', admin.site.urls),
     
     path('<int:id>/', TenantView.as_view(),
          name='tenant-detail-update-delete'),
     
     path('register/', RegisterTenant.as_view(), name='tenat-register'),
     path('otp/', SendOTPView.as_view(), name="send_otp"),
     path("login/", LoginView.as_view()),
     path('api/token/refresh/', MyTokenRefreshView.as_view(),
          name='token_refresh'),
     path('resend-otp/', resend_otp_view, name='resend- otp'),
     path('logout/', logout_user, name='logout'),
     path('company_details/<int:company_id>', CompanydetailView.as_view(),
          name='company_details'),
     path('tenant-access/', handle_active, name='tenant-access/'),
     path('webhooks/stripe/', webhook_handler.stripe_webhook, name='stripe-webhook'),

   
]


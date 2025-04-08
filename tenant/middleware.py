from django_tenants.utils import get_tenant_model, get_tenant_domain_model
import datetime
from django.http import JsonResponse
from django_tenants.middleware import TenantMainMiddleware
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken, AuthenticationFailed
from django.db import connection
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

class CustomTenantMiddleware(TenantMainMiddleware):
    """Tenant detection middleware for multi-tenant support using JWT"""

    def __call__(self, request):
        tenant_model = get_tenant_model()
        domain_model = get_tenant_domain_model()
        host = request.get_host().split(":")[0]

        if request.path.startswith("/admin/") or request.path.startswith("/static/") or request.path.startswith("/media/"):
            connection.set_schema_to_public()
 
            return super().__call__(request)


        try:
            if request.path in ["/api/token/refresh/", "/api/token/employee_refresh/"]:
                logger.info(f"Allowing token refresh request to pass through: {request.path}")
                return super().__call__(request)
            domain = domain_model.objects.get(domain=host)
            tenant = tenant_model.objects.get(id=domain.tenant.id)
            connection.set_tenant(tenant)
            request.tenant = tenant
            print(f"Allowing token refresh request to pass through: {request.path}")
            

            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                print(token)

                try:
                    decoded_token = AccessToken(token)
                    request.user_id = decoded_token["user_id"]
                    request.role = decoded_token.get("role", None)
                    request.permissions = decoded_token.get("permissions", [])
                    request.subdomain = decoded_token.get("subdomain", None)
                except Exception as e:
                    
                        print("Invalid or expired token")
                        return JsonResponse({"error": "Invalid or expired token"}, status=status.HTTP_401_UNAUTHORIZED)

            return super().__call__(request)

        except domain_model.DoesNotExist:
            connection.set_schema_to_public()
            request.tenant = None
            return super().__call__(request)

        except tenant_model.DoesNotExist:
            return JsonResponse({"error": "Tenant not found"}, status=404)

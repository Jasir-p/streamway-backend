from django_tenants.utils import get_tenant_model, get_tenant_domain_model
from asgiref.sync import sync_to_async
from django.db import connection
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

TenantModel = get_tenant_model()
DomainModel = get_tenant_domain_model()
PUBLIC_DOMAINS = ["streamway", "api"]
class CustomTenantMiddleware:
    """Tenant detection middleware for HTTP requests"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'is_async') and request.is_async:
            return self._handle_async_request(request)
        return self._handle_sync_request(request)

    def _handle_sync_request(self, request):
        host = request.get_host().split(".")[0]
        print(host)
        if host in PUBLIC_DOMAINS or request.get_host() in ["streamway.solutions", "api.streamway.solutions"]:
            connection.set_schema_to_public()
            request.tenant = None
            return self.get_response(request)
        if request.path.startswith(("/admin/", "/static/", "/media/")):
            connection.set_schema_to_public()
            return self.get_response(request)

        try:
            if request.path in ["/api/token/refresh/", "/api/token/employee_refresh/"]:
                return self.get_response(request)

            domain = DomainModel.objects.get(domain=host)
            tenant = TenantModel.objects.get(id=domain.tenant.id)
            connection.set_tenant(tenant)
            request.tenant = tenant

            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    token = auth_header.split(" ")[1]
                    decoded_token = AccessToken(token)
                    request.user_id = decoded_token["user_id"]
                    request.role = decoded_token.get("role")
                    request.permissions = decoded_token.get("permissions", [])
                    request.subdomain = decoded_token.get("subdomain")
                except Exception as e:
                    logger.error(f"Token error: {str(e)}")
                    return JsonResponse({"error": "Invalid or expired token"}, status=status.HTTP_401_UNAUTHORIZED)

            return self.get_response(request)

        except DomainModel.DoesNotExist:
            connection.set_schema_to_public()
            request.tenant = None
            return self.get_response(request)

        except TenantModel.DoesNotExist:
            return JsonResponse({"error": "Tenant not found"}, status=404)

    async def _handle_async_request(self, request):
        host = request.get_host().split(":")[0]

        if request.path.startswith(("/admin/", "/static/", "/media/")):
            connection.set_schema_to_public()
            return await self.get_response(request)

        try:
            if request.path in ["/api/token/refresh/", "/api/token/employee_refresh/"]:
                return await self.get_response(request)

            domain = await sync_to_async(DomainModel.objects.get)(domain=host)
            tenant = await sync_to_async(TenantModel.objects.get)(id=domain.tenant.id)
            connection.set_tenant(tenant)
            request.tenant = tenant
            request.scope["tenant"] = tenant

            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    token = auth_header.split(" ")[1]
                    decoded_token = AccessToken(token)
                    request.user_id = decoded_token["user_id"]
                    request.role = decoded_token.get("role")
                    request.permissions = decoded_token.get("permissions", [])
                    request.subdomain = decoded_token.get("subdomain")
                except Exception as e:
                    logger.error(f"Token error: {str(e)}")
                    return JsonResponse({"error": "Invalid or expired token"}, status=status.HTTP_401_UNAUTHORIZED)

            return await self.get_response(request)

        except DomainModel.DoesNotExist:
            connection.set_schema_to_public()
            request.tenant = None
            return await self.get_response(request)

        except TenantModel.DoesNotExist:
            return JsonResponse({"error": "Tenant not found"}, status=404)


from django_tenants.utils import get_tenant_model, get_tenant_domain_model
from asgiref.sync import sync_to_async
from django.db import connection
from urllib.parse import parse_qs

from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from users.models import User  # Adjust if you're using a custom user model

import logging
logger = logging.getLogger(__name__)

TenantModel = get_tenant_model()
DomainModel = get_tenant_domain_model()

class WebSocketTenantMiddleware:
    """Middleware for tenant-aware, JWT-authenticated WebSocket connections."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "websocket":
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers", []))
        host_header = headers.get(b"host", b"").decode("utf-8").split(".")[0]
        logger.info(f"WebSocket host: {host_header}")

        # --- Tenant Resolution ---
        tenant = await self.get_tenant_from_hostname(host_header)
        if tenant:
            scope["tenant"] = tenant
            logger.info(f"Tenant schema set: {tenant.schema_name}")
        else:
            logger.warning(f"No tenant found for host: {host_header}")
            scope["tenant"] = None
            await self.set_schema_to_public_async()

        # --- JWT Authentication ---
        try:
            query_string = scope.get("query_string", b"").decode()
            token = parse_qs(query_string).get("token")

            if token:
                access_token = AccessToken(token[0])
                user = await sync_to_async(User.objects.get)(id=access_token["user_id"])
                scope["user"] = user
                logger.info(f"Authenticated WebSocket user: {user}")
            else:
                scope["user"] = AnonymousUser()
                logger.warning("No token found in WebSocket query string")
        except Exception as e:
            logger.error(f"JWT auth error in WebSocket: {str(e)}")
            scope["user"] = AnonymousUser()

        # Continue with application
        return await self.app(scope, receive, send)

    @sync_to_async
    def get_tenant_from_hostname(self, hostname):
        try:
            connection.set_schema_to_public()
            domain = DomainModel.objects.get(domain=hostname)
            tenant = domain.tenant
            connection.set_tenant(tenant)
            return tenant
        except (DomainModel.DoesNotExist, TenantModel.DoesNotExist):
            connection.set_schema_to_public()
            return None
        except Exception as e:
            logger.error(f"Error resolving tenant: {e}")
            connection.set_schema_to_public()
            return None

    @sync_to_async
    def set_schema_to_public_async(self):
        connection.set_schema_to_public()
        return True

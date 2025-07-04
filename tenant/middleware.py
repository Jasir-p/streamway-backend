# middleware.py
from django_tenants.utils import get_tenant_model, get_tenant_domain_model
from django.db import connection
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import status
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs
from users.models import User
import logging

logger = logging.getLogger(__name__)

TenantModel = get_tenant_model()
DomainModel = get_tenant_domain_model()


class CustomTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info(f"[Middleware] Tenant path: {request.path}")
        path_parts = request.path.strip("/").split("/")
        tenant_prefix = path_parts[0] if path_parts else None
        logger.info(f"[Middleware] Tenant Prefix: {tenant_prefix}")

        # Allow public and static paths
        if request.path.startswith((
            "/admin/", "/static/", "/media/", "/action/",
            "/api/token", "/ws"
        )):
            connection.set_schema_to_public()
            return self.get_response(request)

        try:
            # Ensure we're in public schema when looking up tenant
            connection.set_schema_to_public()
            
            domain = DomainModel.objects.get(domain=tenant_prefix)
            tenant = domain.tenant
            connection.set_tenant(tenant)
            request.tenant = tenant
            request.tenant_prefix = tenant_prefix

            # Strip tenant prefix from request.path_info and request.path
            path_info = request.path_info or request.path
            stripped_path = "/" + "/".join(path_parts[1:]) if len(path_parts) > 1 else "/"
            
            # Preserve trailing slash if it exists in original path
            if request.path.endswith('/') and not stripped_path.endswith('/') and stripped_path != '/':
                stripped_path += '/'
            
            # Update both path_info and path to ensure consistency
            request.path_info = stripped_path
            request.path = stripped_path
            
            # Also update META for consistency
            request.META['PATH_INFO'] = stripped_path
            
            logger.info(f"[Middleware] Original path: {request.path}")
            logger.info(f"[Middleware] Updated path_info: {request.path_info}")
            logger.info(f"[Middleware] Updated path: {request.path}")
            logger.info(f"[Middleware] Tenant: {tenant.schema_name if hasattr(tenant, 'schema_name') else tenant}")

            # Handle JWT token from header (Bearer token)
            token = None
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split("Bearer ")[1]
            elif "access_token" in request.COOKIES:
                token = request.COOKIES["access_token"]

            if token:
                try:
                    decoded_token = AccessToken(token)
                    request.user_id = decoded_token.get("user_id")
                    request.role = decoded_token.get("role")
                    request.permissions = decoded_token.get("permissions", [])
                    logger.info(f"Authenticated user {request.user_id} from token.")
                except Exception as e:
                    logger.warning(f"JWT decode error: {e}")
                    return JsonResponse({"error": "Invalid or expired token"}, status=status.HTTP_401_UNAUTHORIZED)

            return self.get_response(request)

        except DomainModel.DoesNotExist:
            logger.warning(f"No tenant for prefix: {tenant_prefix}")
            connection.set_schema_to_public()
            return self.get_response(request)

        except TenantModel.DoesNotExist:
            logger.error("Tenant not found.")
            return JsonResponse({"error": "Tenant not found"}, status=404)
        except Exception as e:
            logger.exception(f"Unexpected error in tenant middleware: {e}")
            connection.set_schema_to_public()
            return JsonResponse({"error": "Internal server error"}, status=500)


class WebSocketTenantMiddleware:
    """
    WebSocket middleware for multitenancy using subfolder-like prefix.
    Strips tenant prefix from path and authenticates via Bearer token / cookie / query param.
    Example: ws://localhost:8000/adscompany01/ws/notification/
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "websocket":
            return await self.app(scope, receive, send)

        try:
            path_parts = scope.get("path", "/").strip("/").split("/")
            tenant_prefix = path_parts[0] if path_parts else None
            logger.info(f"[WebSocket] Tenant prefix: {tenant_prefix}")

            # Resolve tenant from prefix
            tenant = await self.get_tenant_from_prefix(tenant_prefix)
            if tenant:
                scope["tenant"] = tenant
                # Set tenant context for this connection
                await self.set_tenant_async(tenant)

            # Strip the tenant prefix from path for routing
            new_path = "/" + "/".join(path_parts[1:]) if len(path_parts) > 1 else "/"
            if  not new_path.endswith('/') and new_path!= '/':
                new_path += '/'
            scope["path"] = new_path
            logger.info(f"[WebSocket] Updated path: {scope['path']}")

            # Token extraction (priority: header > query > cookie)
            token = await self.extract_token_from_scope(scope)

            # Attach user to scope
            if token:
                try:
                    access_token = AccessToken(token)
                    user_id = access_token.get("user_id")
                    if user_id:
                        user = await self.get_user_by_id(user_id)
                        scope["user"] = user if user else AnonymousUser()
                        logger.info(f"[WebSocket] Authenticated user {user_id}")
                    else:
                        scope["user"] = AnonymousUser()
                except Exception as e:
                    logger.warning(f"[WebSocket] Token decode/user fetch failed: {e}")
                    scope["user"] = AnonymousUser()
            else:
                scope["user"] = AnonymousUser()

        except Exception as e:
            logger.exception(f"[WebSocket] Unexpected middleware error: {e}")
            scope["user"] = AnonymousUser()
            await self.set_schema_to_public_async()

        return await self.app(scope, receive, send)

    async def extract_token_from_scope(self, scope):
        """Extract token from headers, query params, or cookies"""
        token = None
        
        # 1. From headers
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ")[1]

        # 2. From query params
        if not token:
            query_string = scope.get("query_string", b"").decode()
            if query_string:
                query_params = parse_qs(query_string)
                token = query_params.get("token", [None])[0]

        # 3. From cookies
        if not token and b"cookie" in headers:
            cookies = headers[b"cookie"].decode().split("; ")
            for cookie in cookies:
                if cookie.startswith("access_token="):
                    token = cookie.split("=", 1)[1]
                    break

        return token

    @sync_to_async
    def get_tenant_from_prefix(self, prefix):
        """Get tenant from prefix, ensuring proper schema switching"""
        try:
            # Always start from public schema for tenant lookup
            connection.set_schema_to_public()
            domain = DomainModel.objects.get(domain=prefix)
            tenant = domain.tenant
            return tenant
        except (DomainModel.DoesNotExist, TenantModel.DoesNotExist) as e:
            logger.error(f"[WebSocket] Tenant resolve error: {e}")
            return None
        except Exception as e:
            logger.exception(f"[WebSocket] Unexpected tenant resolve error: {e}")
            return None

    @sync_to_async
    def set_schema_to_public_async(self):
        """Set database schema to public"""
        connection.set_schema_to_public()

    @sync_to_async
    def set_tenant_async(self, tenant):
        """Set database schema to tenant"""
        connection.set_tenant(tenant)

    @sync_to_async
    def get_user_by_id(self, user_id):
        """Get user by ID from current tenant schema"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.warning(f"[WebSocket] User {user_id} not found in tenant schema")
            return None
        except Exception as e:
            logger.exception(f"[WebSocket] Error fetching user {user_id}: {e}")
            return None
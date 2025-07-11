from django.shortcuts import render
from tenant.serializer import TenantSerializer,CustomTokenObtainPairSerializer,CustomTokenRefreshSerializer,TenantViewSerializer
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from .models import Tenant, Domain
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .utlis.otp_utils import generate_otp, validate_otp
from .tasks import send_otp_email_task,send_login_credential
from django.conf import settings
import redis
import json
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django.db import connection,transaction
from django.http import HttpResponse
from django_tenants.utils import connection
from django.http import JsonResponse
from django.contrib.auth.models import User  # If users exist in Django
from django.shortcuts import get_object_or_404
from django_tenants.utils import schema_context, get_tenant_model, get_tenant_domain_model
import logging
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from users.models import Employee
from .pagination import StandardResultsSetPagination
from admin_panel.tasks import log_user_activity_task

logger = logging.getLogger(__name__)

redis_client = redis.StrictRedis(host='redis', port=6379, db=0,
                                 decode_responses=True)


# ----------------- OTP Section --------------


class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp, expiray_minute = generate_otp(email)

        if otp:
            send_otp_email_task.delay(email, otp)
            return Response(
                {"message": "OTP sent successfully"}, status=status.HTTP_200_OK
            )
        return Response({"error": " Failed to send otp, pleae try again"},
                        status=status.HTTP_400_BAD_REQUEST)


def sentotp(email):
    
    if not email:
        return Response(
            {"error": "Email is required"},
            status=status.HTTP_400_BAD_REQUEST
            )

    otp, expiray_minute = generate_otp(email)

    if otp:
        send_otp_email_task.delay(email, otp)
        return Response(
            {"message": "OTP sent successfully"}, status=status.HTTP_200_OK
                )
    return Response({"error": " Failed to send otp, pleae try again"},
                    status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def resend_otp_view(request):
    email = request.data.get("email")
    if not email:
        return Response({"error": "Email is required"},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        key = f"otp_{email}"
        otp_data = redis_client.hgetall(key)
        if otp_data:
            redis_client.delete(key)

        otp, expiray_minute = generate_otp(email)
        send_otp_email_task.delay(email, otp)
        return Response({"message": "OTP sent successfully"}, 
                        status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TenantView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        elif self.request.method in ['GET', 'PUT', 'DELETE']:
            # return [IsAuthenticated()] 
            return [AllowAny()]
        return super().get_permissions()
    
    

    def get(self, request, id=None):
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
           
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                with schema_context(tenant.schema_name):
                    tenant_user_count = Employee.objects.count()
                
                serializer = TenantViewSerializer(tenant)
                tenant_data = serializer.data
                tenant_data['user_count']= tenant_user_count
                return Response(tenant_data, status=status.HTTP_200_OK)
            except Tenant.DoesNotExist:
                return Response(
                    {"error": "Tenant not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            tenant_user_count = {}
            tenants = Tenant.objects.all().order_by("id")

            for tenant in tenants:
                with schema_context(tenant.schema_name):
                    tenant_user_count[tenant.id] = Employee.objects.count()
            paginator = StandardResultsSetPagination()
            paginator.page_size = 10
            result_page = paginator.paginate_queryset(tenants, request)
            serialize_data = TenantViewSerializer(result_page, many=True).data
            for tenany in serialize_data:
                tenany['user_count'] = tenant_user_count[tenany['id']]
                                
            return paginator.get_paginated_response(serialize_data)
            

    def post(self, request, format=None):
        tenantdata = request.data

        if not tenantdata:
            return Response({"error": "Data is Required"})
        
        email = request.data.get('email')
        try:


            serializer = TenantSerializer(data=tenantdata)
            if serializer.is_valid():
                redis_key = f"tenant_data:{email}"
                redis_client.set(redis_key,
                                 json.dumps(serializer.validated_data))
                redis_client.expire(redis_key, 1200)
                sentotp(email)
                return Response({"message": "Data is stored Succesfully"}, 
                                status=status.HTTP_200_OK)

            return Response(serializer.errors, 
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:

            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request,format=None):

            tenant_id = request.query_params.get("tenant_id")
            if not tenant_id:
                return Response({"error": "Tenant ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                tenant = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                return Response({"error": "Tenant not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = TenantSerializer(tenant, data=request.data, partial=True) 
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):
        # Delete a tenant

        try:
            tenant = Tenant.objects.get(id=id)
            tenant.delete()
            return Response(
                {"message": "Tenant deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Tenant.DoesNotExist:
            return Response(
                {"error": "Tenant not found"}, status=status.HTTP_404_NOT_FOUND
            )


class RegisterTenant(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")


        if not email or not otp:
            return Response({"error": "Email and OTP are required"}, 
                            status=status.HTTP_400_BAD_REQUEST)

        redis_key = f"tenant_data:{email}"
        tenant_data = redis_client.get(redis_key)

        if not tenant_data:
            return Response({"error": "Data not found in cache"}, 
                            status=status.HTTP_404_NOT_FOUND)

        tenant_data = json.loads(tenant_data)

        try:
            # Validate OTP
            is_valid, message = validate_otp(email, otp)
            if not is_valid:
                return Response({"error": message}, 
                                status=status.HTTP_400_BAD_REQUEST)

            # Save tenant data to the database
            serializer = TenantSerializer(data=tenant_data)
            if serializer.is_valid():
                
                tenant = serializer.save()
                log_user_activity_task(tenant.name,"Tenant created")
                
                # Create a domain for the tenant
                domain_name = f"{tenant.schema_name}"
                Domain.objects.create(
                    domain=domain_name,
                    tenant=tenant,
                    is_primary=True
                )
               
                redis_client.delete(redis_key)

                redis_key = f"password:{email}"
                generated_password = redis_client.hget(
                    redis_key, 'generated_password'
                )
                send_login_credential.delay(email, generated_password)
                redis_client.delete(redis_key)

                return Response({"message": "Tenant registered successfully"},
                                status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, 
                                status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:

            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


Tenant = get_tenant_model()
Domain = get_tenant_domain_model()


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        

        try:

            user = authenticate(request, username=username, password=password)

            if not user:
                return Response({"error": "Invalid credentials."}, 
                                status=status.HTTP_401_UNAUTHORIZED)
            
            with schema_context("public"):
                tenant = get_object_or_404(Tenant, email=user.username)
                domain = get_object_or_404(Domain, tenant=tenant)
            if not tenant.is_active:
                return Response({"error": "Your account is deactivated."}, status=status.HTTP_403_FORBIDDEN)

            user_profile = TenantSerializer(tenant)

            token_serializer = CustomTokenObtainPairSerializer.get_token(user)

            access_token = token_serializer.access_token
            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Login successful",
                "access_token": str(access_token),  
                "refresh_token": str(refresh),
                "profile": user_profile.data
            }, status=200)

        except Exception as e:
            logger.error(str(e))
            return Response({"error": str(e)}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckAuthView(APIView):
    """
     API to check:
      1️ If the subdomain (tenant) exists (For unauthenticated users)
      2️ If the user is authenticated & token is valid (For logged-in users)
    """
    permission_classes = [AllowAny]

    def get(self, request):

        host = request.get_host().split(".")[0]
        subdomain = host.split(".")[0] if "." in host else None

        try:
            domain = Domain.objects.get(domain=host)
            tenant = Tenant.objects.get(id=domain.tenant.id)
            connection.set_tenant(tenant)
        except (Domain.DoesNotExist, Tenant.DoesNotExist):
            return JsonResponse({"status": False, "message": "Tenant not found"}, status=404)
    
        auth = request.headers.get("Authorization")

        if not auth or not auth.startswith("Bearer "):
            return JsonResponse({
                "status": True, 
                "message": "Tenant exists", 
                "subdomain": subdomain
            }, status=200)  
        token = auth.split(" ")[1]

        try:

            decoded_token = AccessToken(token)
            token_subdomain = decoded_token.get("subdomain")

            if token_subdomain != subdomain:
                return JsonResponse({"status": False, "message": "Subdomain mismatch"}, status=403)

            return JsonResponse({
                "status": True,
                "message": "User authenticated",
                "user_id": decoded_token["user_id"],
                "role": decoded_token.get("role", None),
                "permissions": decoded_token.get("permissions", []),
                "subdomain": subdomain
            })

        except Exception as e:
            
            error_message = str(e)
            if "Token is invalid or expired" in error_message:
                return JsonResponse({"status": False, "message": "Token expired"}, status=401)
            return JsonResponse({"status": False, "message": "Invalid token"}, status=401)
        

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_user(request):
    try:
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return JsonResponse({"status": False, "message": "Refresh token not found"}, status=400
                                )

        token = RefreshToken(refresh_token)
        token.blacklist()
        return JsonResponse({"status": True, "message": "User logged out"},
                            status=200)
    except Exception as e:
        error_message = str(e)
        return JsonResponse({"status": False, "message": error_message},
                            status=400)


class CompanydetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        try:
            with schema_context("public"):
                company_details = get_object_or_404(Tenant, id=company_id)
            
            company_serializer = TenantSerializer(company_details)
            
            employee_count = Employee.objects.count()
            return JsonResponse({"company":company_serializer.data,
                                 "employee_count": employee_count}, status=200)
        except Exception as e:
            error_message = str(e)
            return JsonResponse({"status": False, "message": error_message}, status=400)
        
    def put(self, request, company_id):
        try:
            with schema_context("public"):
                company_details = get_object_or_404(Tenant, id=company_id)
            current_user_email = company_details.email
            new_email = request.data.get("email")
            if not new_email:
                return JsonResponse(
                    {"status": False, "message": "Email not found"}, status=400
                )
            if new_email == current_user_email:
                pass
            with transaction.atomic():
                user_instance = get_object_or_404(
                    User, username=current_user_email
                )

                company_serializer = TenantSerializer(
                    company_details, data=request.data, partial=True)
                if company_serializer.is_valid():
                    user_instance.username = new_email
                    user_instance.save()
                    company_serializer.save()
                    return JsonResponse(
                        {"status": True, "message": "Company details updated"},
                        status=200
                    )
                return JsonResponse(
                    {"status": False, "message": company_serializer.errors},
                    
                    status=400
                )
        except Exception as e:
            error_message = str(e)
            return JsonResponse(
                {"status": False, "message": error_message}, status=400
            )
        


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class MyTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer



@api_view(["PATCH"])
@permission_classes([AllowAny])
def handle_active(request):
    tenant_id = request.data.get("tenant_id")

    if not tenant_id:
        return Response({"error": "Tenant ID is required"}, status=400)

    try:
        tenant = Tenant.objects.get(id=int(tenant_id)) 
        tenant.is_active = not tenant.is_active
        tenant.save()
        return Response({"success": True, "is_active": tenant.is_active})
    except Tenant.DoesNotExist:
        return Response({"error": "Tenant not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
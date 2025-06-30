from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from tenant.models import Tenant,TenantBilling,Invoice
from billing.serializers import InvoiceSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
import redis
import json



redis_client = redis.StrictRedis(host='redis', port=6379, db=0,
                                 decode_responses=True)


# Create your views here.
@api_view(["POST"])
@permission_classes([AllowAny])
def admin_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    try:
        user = User.objects.get(username=username)
        if user.is_superuser and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            refresh['role']= 'admin'
            refresh['subdomain'] = None
            
            return Response({"message": "Admin logged in successfully",
                             'access_token':str(refresh.access_token),
                            'refresh':str(refresh)
                            }, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"message": "Invalid username or password"}, status=status.HTTP_404_NOT_FOUND)
    

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    try:
        key = "active_logs"
        logs_json = redis_client.get(key)

        if logs_json:
            logs = json.loads(logs_json)
            logs = logs[:5]
        else:
            logs = []

        tenats_count = Tenant.objects.all().count()
        invoice_data =InvoiceSerializer(Invoice.objects.all(), many=True)
        return Response({
            "tenants_count":tenats_count,
            "invoices":invoice_data.data,
            "logs":logs
        },status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message":str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_analytics(request):
    try:
        invoice_data =InvoiceSerializer(Invoice.objects.all(), many=True)
        return Response({
         
            "invoices":invoice_data.data
        },status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message":str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_admin(request):
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_active_logs(request):
    key = "active_logs"
    logs_json = redis_client.get(key)

    if logs_json:
        logs = json.loads(logs_json)
    else:
        logs = []
    print(logs)
    return JsonResponse({"logs": logs})
    
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from tenant.models import Tenant,TenantBilling,Invoice
from billing.serializers import InvoiceSerializer
# Create your views here.
@api_view(["POST"])
@permission_classes([AllowAny])
def admin_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    try:
        user = User.objects.get(username=username)
        if user.is_superuser and user.check_password(password):
            return Response({"message": "Admin logged in successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"message": "Invalid username or password"}, status=status.HTTP_404_NOT_FOUND)
    

@api_view(["GET"])
@permission_classes([AllowAny])
def admin_dashboard(request):
    try:
        tenats_count = Tenant.objects.all().count()
        invoice_data =InvoiceSerializer(Invoice.objects.all(), many=True)
        return Response({
            "tenants_count":tenats_count,
            "invoices":invoice_data.data
        },status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message":str(e)}, status=status.HTTP_400_BAD_REQUEST)


    




        
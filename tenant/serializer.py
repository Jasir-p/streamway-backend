from rest_framework import serializers
from .models import Tenant,Domain
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer,TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django_tenants.utils import get_tenant_model, get_tenant_domain_model, schema_context
from django.shortcuts import get_object_or_404
from django.db import connection
import logging
import re

logger = logging.getLogger(__name__)
EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
CONTACT_REGEX = r"^(?!0{10})[0-9]{10}$"
NAME_REGEX = r"^(?=.*[A-Za-z])[A-Za-z0-9\s&.,'-]+$"
class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'email', 'owner_name', 'contact',
            'auto_created_schema', 'is_active',
            'created_on', 'trial_period_days'
        ]
        extra_kwargs = {
            'name': {'required': True},
            'owner_name': {'required': True},
        }
        read_only_fields = [
            'created_on', 'trial_period_days',
            'auto_created_schema', 'is_active', 'schema_name', 
            'auto_drop_schema'
        ]
    def validate_owner_name(self, value):
        value=value.strip()
        if not value:
            raise serializers.ValidationError('Owner name is required')
        if not re.match(NAME_REGEX, value):
            raise serializers.ValidationError('Invalid owner name')
        return value
    def validate_name(self, value):
        
        " Validate the name of the tenant "
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Tenant name cannot be empty")
        if not re.match(NAME_REGEX, value):
            raise serializers.ValidationError("Invalid tenant name")
        return value

    def validate_email(self, value):
        """Validate the email format and uniqueness."""
        if not re.match(EMAIL_REGEX, value):
            raise serializers.ValidationError('Invalid email format')
        if not value.endswith("com"):
            raise serializers.ValidationError
        ("The email must belong to the 'example.com' domain.")
        tenant_id = self.instance.id if self.instance else None
        if Tenant.objects.filter(email=value).exclude(id=tenant_id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_contact(self, value):
        """Validate the contact number format and length."""
        if not re.match(CONTACT_REGEX, value):
            raise serializers.ValidationError("Enter a valid 10-digit contact number (not all zeros).")
        return value

    def create(self, validated_data):
        """Create a new tenant with additional logic if required."""
       
        return Tenant.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update an existing tenant """
      
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


Tenants = get_tenant_model()
Domains = get_tenant_domain_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT Token Serializer with Tenant, Role, and Permissions"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["name"] = user.username
        token["role"] = "owner"

        try:
           
            with schema_context("public"):
                tenant = get_object_or_404(Tenants, email=user.username)  
                domain = get_object_or_404(Domains, tenant=tenant)
                
            token["subdomain"] = domain.domain.split(".")[0] 

            token["tenant_name"] = tenant.name
            

        except Tenants.DoesNotExist:
            token["subdomain"] = None
            token["tenant_name"] = None

        return token
    

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """Ensure `subdomain` and `tenant_name` are included inside the new access token"""

    def validate(self, attrs):
        data = super().validate(attrs)  # This will validate the refresh token and create a new access token
 
        access_token = AccessToken(data["access"])
        
        user_id = access_token["user_id"]
        print("user",user_id)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
  
            with schema_context("public"):
                tenant = Tenants.objects.get(email=user.username)  
                domain = Domains.objects.get(tenant=tenant)

            access_token["name"] = user.username
            access_token["role"] = "owner"
            access_token["subdomain"] = domain.domain.split(".")[0]
            access_token["tenant_name"] = tenant.name

            data["access"] = str(access_token)
            
        except (User.DoesNotExist, Tenants.DoesNotExist, Domains.DoesNotExist) as e:
            
            logger.error(f"Error fetching tenant data: {e}")
            
        return data


class TenantViewSerializer(serializers.ModelSerializer):
    class Meta:
         model = Tenant
         fields = '__all__'
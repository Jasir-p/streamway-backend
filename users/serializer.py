from rest_framework import serializers
from .models import Employee, Team, TeamMembers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer,TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.db import connection
from django.contrib.auth.models import User
from rabc.serializers import RoleSerializers
from rabc.models import RoleAcessPermission
from django.contrib.auth.hashers import make_password




class EmployeeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employee
        fields = [
            'id', 'name', 'email', 'role'
        ]

        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True},
            'role': {'required': True}
        }

    def validate_email(self, value):
        if not value.endswith(".com"):
            raise serializers.ValidationError("Invalid email format")
        employe_id = self.instance.id if self.instance else None
        if Employee.objects.filter(email__iexact=value).exclude(id=employe_id).exists():
            raise serializers.ValidationError("email already exist")
        
        return value
    
    def create(self, validated_data):
        user_data = validated_data.pop("user", None)
        if user_data:
            user = user_data
        else:
            user = User.objects.create_user(
                username=validated_data['email'],
                password="12345678"
            )

        employee = Employee.objects.create(user=user, **validated_data)
        return employee
    def update(self, instance, validated_data):
        
        try:
            # Directly update fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()
            return instance
        except Exception as e:
            print("Error during update:", e)
            raise serializers.ValidationError({"error": str(e)})

         
class UserListViewSerializer(serializers.ModelSerializer):
    role = RoleSerializers(read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'name', 'email', 'role', "user", "is_active"]


class CustomEmployeeTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT Token Serializer for Employee"""

    @classmethod
    def get_token(cls, employee):
        emp = Employee.objects.get(user=employee)

        token = super().get_token(employee)

        token["name"] = emp.name
        token["role"] = emp.role.name if emp.role else None
        token["email"] = emp.email
        token["permissions"] = list(RoleAcessPermission.objects.filter(role=emp.role).values_list("Permission__code_name", flat=True))
        tenant_name = connection.tenant.name
        subdomain = connection.tenant.domain_url.split(".")[0]

        token["subdomain"] = subdomain

        token["tenant_name"] = tenant_name
       
        return token
    

class CustomRefreshSerializer(TokenRefreshSerializer):
    """Custom JWT Token Refresh Serializer for Employee"""
    def validate(self, attrs):
        data = super().validate(attrs)  
 
        access_token = AccessToken(data["access"])
        user_id = access_token["user_id"]
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)

            employee =Employee.objects.get(user=user)
            
            access_token["name"] = employee.name
            access_token["role"] = employee.role.name if employee.role else None
            access_token["email"] = employee.email
            access_token["permissions"] = list(RoleAcessPermission.objects.filter(role=employee.role).values_list("Permission__code_name", flat=True))
            tenant_name = connection.tenant.name
            subdomain = connection.tenant.domain_url.split(".")[0]
            access_token["tenant_name"] = tenant_name
            access_token["subdomain"] = subdomain
            data["access"] = str(access_token)
            
        except (User.DoesNotExist, Employee.DoesNotExist) as e:
            pass
            
        return data

    




class TeamSerializer(serializers.ModelSerializer):
    members = EmployeeSerializer(many=True, read_only=True)
    team_lead = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'created_by',
                  'created_at', 'updated_at', 'team_lead', 'members']
        
        extra_kwargs = {'name': {'required': True},
                        'description': {'required': True},
                        'team_lead': {'required': True}
                        
                        }
        
    def validate_name(self, value):
        if Team.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Team name already exists")
        return value
        
    def create(self, validated_data):
        team = Team.objects.create(**validated_data)
        return team
  
        
class TeamViewserilizer(serializers.ModelSerializer):
    members = EmployeeSerializer(many=True, read_only=True)
    team_lead = EmployeeSerializer(read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'created_by',
                  'created_at', 'updated_at', 'team_lead', 'members']
        


class TeamMembersSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMembers
        fields = ['id', 'team', 'employee', 'joined_at']

    def validate_employee(self, value):
        if TeamMembers.objects.filter(employee=value).exists():
            raise serializers.ValidationError("Employee already exists in the team")
        return value
        
    def create(self, validated_data):
        return TeamMembers.objects.create(**validated_data)


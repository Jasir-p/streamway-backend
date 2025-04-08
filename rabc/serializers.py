from rest_framework import serializers
from .models import Role, TenantPermission, RoleAcessPermission


class RoleSerializers(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = [
                'id', 'name', 'description', 'parent_role'
            ]
        extra_kwargs = {
                'name': {'required': True},
            
            }
        
    def validate_name(self, value):
        role_id = self.instance.id if self.instance else None
        if Role.objects.filter(name__iexact=value).exclude(
             id=role_id).exists():
            raise serializers.ValidationError("The name already exists")
        return value
 
    def update(self, instance, validated_data):
        """Update exisiting Role"""
        
        for attr, value in validated_data.items():
            print(attr, value)
            setattr(instance, attr, value)
        instance.save()
        return instance


class PermissionSerializer(serializers.ModelSerializer):
     
    class Meta:
        model = TenantPermission
        fields = ["id", "name", "code_name", "module"]


class RoleAcessPermissionReadSerializer(serializers.ModelSerializer):
    Permission = PermissionSerializer(read_only=True)  # Read-only Permission

    class Meta:
        model = RoleAcessPermission
        fields = ["id", "role", "Permission"]
        

class RoleAcessPermissionSerializer(serializers.ModelSerializer):
    
    class Meta: 
        model = RoleAcessPermission
        fields = ["id", "role", "Permission"]

    def validate(self, attrs):
        role = attrs.get('role')
        permission = attrs.get('Permission')
        if RoleAcessPermission.objects.filter(
                role=role, Permission=permission).exists():
            raise serializers.ValidationError(
                "The role already has this permission"
            )
        return attrs
        

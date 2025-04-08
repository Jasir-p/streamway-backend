from rest_framework.views import APIView
from .models import Role, TenantPermission, RoleAcessPermission
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
# from django_tenants.utils import schema_context
# from django.conf import settings
from .serializers import RoleSerializers, PermissionSerializer, RoleAcessPermissionSerializer, RoleAcessPermissionReadSerializer
from rest_framework.generics import ListAPIView
from users.models import Employee
from users.serializer import UserListViewSerializer


class RoleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        id = request.query_params.get("role_id")
        print(id)
        if id:
            return self.get_role(request, id)

        # Fetch only top-level roles
        roles = Role.objects.filter(parent_role__isnull=True)  
        hierarchy = [role.get_role_hierarchy() for role in roles]
        for role in roles:
            print(role.get_role_hierarchy())
        
        return Response({"roles": hierarchy})
            
    def get_role(self, request, id):
        try:       
            role = Role.objects.get(id=id)
            serializer = RoleSerializers(role)
            print(serializer.data)
            employees = Employee.objects.filter(role__id=role.id)
            employee_serializer = UserListViewSerializer(employees, many=True)
            permission = RoleAcessPermission.objects.filter(role__id=id)
            permission_serializer = RoleAcessPermissionReadSerializer(
                permission, many=True)
            return Response({"roles": serializer.data,
                             "permission": permission_serializer.data,
                             "employees": employee_serializer.data},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, format=None):
        print(request.data)
        serializers = RoleSerializers(data=request.data)

        if serializers.is_valid():
            serializers.save()
            return Response({"message": "created"},
                            status=status.HTTP_201_CREATED)
        else:
            print(serializers.errors)
            
            return Response(serializers.errors, 
                            status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request,  format=None):
        id = request.query_params["role_id"]
        if not id:
            return Response({"error": "Role ID is required"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        try:
                      
            role = get_object_or_404(Role, id=id)
            serializers = RoleSerializers(role, data=request.data, 
                                          partial=True)
            
            if serializers.is_valid():
                serializers.save()

                return Response({"message": "Sucessfully Updated"}, 
                                status=status.HTTP_200_OK)
            else:
                return Response({serializers.errors}, 
                                status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, format=None):

        id = request.query_params["role_id"]
        if not id:
            return Response({"error": "Role ID is required"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            
            role = get_object_or_404(Role, id=id)
            role.children.update(parent_role=role.parent_role)
            # role.user_set.update(role=role.parent_role if role.parent_roleelse None)
            role.delete()
            
            return Response(
                {"message": "Roles deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PermissionView(ListAPIView):
    queryset = TenantPermission.objects.all()
    serializer_class = PermissionSerializer


class RoleAcessPermissionView(APIView):

    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        print("data", request.data)
        
        serializer = RoleAcessPermissionSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)  

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, *args, **kwargs):
        print("data", request.data)
        role_id = request.data.get("role")
        perm_id = request.data.get("Permission")

        print(role_id, perm_id)
                
        try:
            
            rbac = get_object_or_404(RoleAcessPermission,
                                     role=role_id, Permission=perm_id)
            rbac.delete()

            return Response({"message": "deleted Succesfully"}, 
                            status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            return Response({"error": str(e)}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        






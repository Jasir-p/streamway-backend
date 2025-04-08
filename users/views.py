
from .serializer import EmployeeSerializer, UserListViewSerializer, TeamSerializer, TeamMembersSerializer,CustomEmployeeTokenObtainPairSerializer,TeamViewserilizer , CustomRefreshSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Employee, Team, TeamMembers
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view,permission_classes
from users.tasks import employee_login_credential, employee_password_change
from django_tenants.utils import get_tenant_model, get_tenant_domain_model
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
import redis
import json
from tenant.utlis.otp_utils import generate_otp, validate_otp
from django_tenants.utils import schema_context
from django.shortcuts import get_object_or_404
from tenant.models import Tenant
from rabc.models import Role
import traceback

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0,
                                 decode_responses=True)

tenant_model = get_tenant_model()
domain_model = get_tenant_domain_model()

# _______EMPLOYEES______


class EmployeeManagment(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            employee = Employee.objects.all()
            serializer = UserListViewSerializer(employee, many=True)
            if serializer.data:
                print(serializer.data)
                
                return Response({'employee': serializer.data},
                                status=status.HTTP_200_OK)
            
            return Response({"message": "No data found"},
                            status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"error": str(e)}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, format=None):
        employeedata = request.data
        if not employeedata:
            return Response({"error": "Data is requuired"})
        
        try:
            serializer = EmployeeSerializer(data=employeedata)
            if serializer.is_valid():
                serializer.save()
                tenant_name = request.tenant.name
                subdomain_instance = domain_model.objects.get(
                    tenant=request.tenant
                )
                subdomain = subdomain_instance.domain.replace(".localhost", "")

                employee_login_credential.delay(serializer.data['email'],
                                                tenant_name, subdomain)

                return Response({"message": "Created Succesfully"},
                                status=status.HTTP_201_CREATED)
            
            return Response({"error": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        try:
            employee = Employee.objects.get(user_id=user_id)
            serializer = EmployeeSerializer(employee, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Updated Succesfully"},
                                status=status.HTTP_200_OK)
            return Response({"error": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        print(user_id)
        try:
            employee = Employee.objects.get(id=user_id)
            employee.user.delete()
            employee.delete()
            return Response({"message": "Deleted Succesfully"},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        print(password, username)
        try:
            employee = authenticate(username=username, password=password)
            
            if not employee:
                return Response({"error": "Invalid credentials."},  
                                status=status.HTTP_401_UNAUTHORIZED)
            
            if not employee.is_active:
                return Response({"error": "Your account has been disabled."},
                                status=status.HTTP_403_FORBIDDEN)
            Employee.objects.get(user=employee)
            token_serializer = CustomEmployeeTokenObtainPairSerializer.get_token(employee)
            access_roken = token_serializer.access_token
            refresh_token = RefreshToken.for_user(employee)
            employee_instance = Employee.objects.get(user=employee)
            employee_serializer = EmployeeSerializer(employee_instance)
            print(employee_serializer.data)

            return Response({"access_token": str(access_roken),
                            "refresh_token": str(refresh_token),
                             "profile": employee_serializer.data}, status=status.HTTP_200_OK)
        except Employee.DoesNotExist:
            print("error")
            return Response({"error": "invalid user"},
                            status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def user_access(request):
    try:

        users_id = request.data.get("user_ids")
        print(users_id)
        if isinstance(users_id, int):
            users_id = [users_id]
        if not users_id:
            return Response({"error": "No user id provided"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        users = Employee.objects.filter(id__in=users_id)

        for user in users:
            user.is_active = not user.is_active
            user.save()
            auth_user = User.objects.get(id=user.user.id)
            auth_user.is_active = not auth_user.is_active
            auth_user.save()

        return Response({"message": "User access updated successfully"}, 
                        status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"error": str(e)}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["POST"])
@permission_classes([AllowAny])
def password_change(request):
    print(request.data)
    try:
        email = request.data.get("email")
        password = request.data.get("confirmPassword")
        tenant_name = request.tenant.name
        if not password:
            return Response({"error": "Password is required"},
                            status=status.HTTP_400_BAD_REQUEST)
        
        User.objects.get(username=email)
        print(User.objects.get(username=email))
        redis_key = f"password:{email}"
        redis_client.set(redis_key, json.dumps(password))
        redis_client.expire(redis_key, 1200)
        otp_data, expire = generate_otp(email)
        print(otp_data)
        employee_password_change.delay(email, otp_data, tenant_name)

        return Response({"message": "OTP sent successfully"}, 
                        status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "Invalid user"},
                        status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print("Exception Traceback:", traceback.format_exc())
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def password_change_verify(request):
    print(request.data)
    try:
        otp = request.data.get("otp")
        email = request.data.get("email")
        if not otp:
            return Response({"error": "OTP is required"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({"error": "Email is required"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        redis_key = f"password:{email}"
        password_data = redis_client.get(redis_key)
        if not password_data:
            return Response({"error": "Invalid OTP"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        password = json.loads(password_data)
        print(email, otp)
        is_valid, message = validate_otp(email, otp)
        
        if not is_valid:
            return Response({"error": message}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.get(username=email)
        user.set_password(password)
        user.save()
        redis_client.delete(redis_key)

        
        return Response({"message": "Password changed successfully"},
                        status=status.HTTP_200_OK)
    
    except Exception as e:
        print("Exception Traceback:", traceback.format_exc())
        return Response({"error": str(e)}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def profile_update(request):
    user_id = request.data.get("userId")
    role = request.data.get("role")
    profile_data = {
        "id": request.data.get("id"),
        "name": request.data.get("name"),
        "email": request.data.get("email"),
        "role": role
    }


    if not user_id:
        return Response({"error": "User ID is required"},
                        status=status.HTTP_400_BAD_REQUEST)
    if not profile_data:
        return Response({"error": "Profile Data is required"},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        if role =="owner":
            with schema_context("public"):
                tenant = get_object_or_404(Tenant, id=user_id)
                tenant.owner_name = profile_data.get('name')
                tenant.save()
                return Response({"message": "Profile updated successfully"},
                                status=status.HTTP_200_OK)
        else:
            user_instnace = Employee.objects.get(id=user_id)
            serializer = EmployeeSerializer(
                instance=user_instnace, data=profile_data, partial=True
            )
            role_instance = Role.objects.filter(name=role).first()
            if not role_instance:
                return Response(
                    {"error": "Invalid role"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            profile_data["role"] = role_instance.id

            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Profile updated successfully"}, status=status.HTTP_200_OK)
            else:
                print(serializer.errors)  # Log the actual errors
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        print("Exception Traceback:", traceback.format_exc())
        return Response({"error": str(e)}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
            

            

    



        

       

class MyTokenObtainPairView(TokenObtainPairView):
    
    serializer_class = CustomEmployeeTokenObtainPairSerializer


class MyTokenRefreshView(TokenRefreshView):

    serializer_class = CustomRefreshSerializer


# ____________TEAM__________
     
class TeamManagmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        team_id = request.query_params.get("team_id")
        print(team_id)
        if team_id:
            return self.get_team(request, team_id)
        try:
            team = Team.objects.all()
            serializer = TeamViewserilizer(team, many=True)
            if serializer.data:
                return Response({"teams": serializer.data})
            return Response({"error": "No team found"})
        except Exception as e:

            return Response({"error": str(e)}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get_team(self, request, team_id):
        try:
            team = Team.objects.get(id=team_id)
            serializer = TeamViewserilizer(team)
            print(serializer.data)
            return Response({"team": serializer.data})
        except Team.DoesNotExist:
            return Response({"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND)
       
    def post(self, request, *args, **kwargs):
        print(request.data["team_lead"])
        try:
            serializer = TeamSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Team created successfully"},
                                status=status.HTTP_201_CREATED)
            return Response({"error": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
  
class TeamMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            team_id = kwargs.get('team_id')
            team = Team.objects.get(id=team_id)
            team_members = team.team_members.all()
            serializer = TeamMembersSerializer(data=team_members)
            if serializer.data:
                return Response({"team_member": serializer.data},
                                status=status.HTTP_200_OK)
             
            return Response({"error": "No team member found"},
                            status=status.HTTP_404_NOT_FOUND)
        
        except Team.DoesNotExist:
            return Response({"error": "Team not found"},
                            status=status.HTTP_404_NOT_FOUND)
        
    def post(self, request, *args, **kwargs):
        print(request.data)
        try:
            serializer = TeamMembersSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Team member created successfully"},
                                status=status.HTTP_201_CREATED)
            print(serializer.errors) 
            return Response({"error": serializer.errors}, 
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, *args, **kwargs):
        try:
            team_id = request.data.get("team_id")
            team = Team.objects.get(id=team_id)
            team.delete()
            return Response({"message": "Team deleted successfully"},
                            status=status.HTTP_200_OK)
        
        except Team.DoesNotExist:
            return Response({"error": "Team not found"},
                            status=status.HTTP_404_NOT_FOUND)
        



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_team_lead(request):

    try:
        team_lead_id = request.data.get("lead_id")
        team_id = request.data.get("team_id")
        if not team_lead_id or not team_id:
            return Response({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)
            
        new_lead = Employee.objects.get(id=team_lead_id)
        team = Team.objects.get(id=team_id)
        if new_lead not in team.members.all():
            return Response({"error": "The selected employee is not a member of this team"}, 
                            status=status.HTTP_400_BAD_REQUEST)

        if team.team_lead == new_lead:
            return Response({"message": "This user is already the team lead"}, 
                            status=status.HTTP_200_OK)
        
        team.team_lead = new_lead
        team.save()
        return Response({"message": "Team lead updated successfully"}, 
                        status=status.HTTP_200_OK)
    except Employee.DoesNotExist:
        return Response({"error": "Employee not found"},
                        status=status.HTTP_404_NOT_FOUND)
    except Team.DoesNotExist:
        return Response({"error": "Team not found"},
                        status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response({"error": str(e)}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


        

        
        

  
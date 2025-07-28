
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
from users.tasks import employee_login_credential, employee_password_change,password_send
from django_tenants.utils import get_tenant_model, get_tenant_domain_model
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
import redis
import json
from tenant.utlis.otp_utils import generate_otp, validate_otp
from tenant.utlis.password_genarator import generate_password
from django_tenants.utils import schema_context
from django.shortcuts import get_object_or_404
from tenant.models import Tenant
from rabc.models import Role
import traceback
from .utlis.employee_hierarchy import get_employee_and_subordinates_ids
from admin_panel.tasks import log_user_activity_task
from activities.serializers import TaskViewSerializer
from tenant.tasks import send_otp_email_task
from tenant_panel.constants import PASSWORD_REGEX
import re

redis_client = redis.StrictRedis(host='redis', port=6379, db=0,
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
                log_user_activity_task.delay(request.tenant.name, 'Employee Created',)

                return Response({"message": "Created Succesfully"},
                                status=status.HTTP_201_CREATED)
            
            return Response({"error": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def put(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        user_data = request.data.get("user_data")

        
        try:
            employee = Employee.objects.get(id=user_id)
            serializer = EmployeeSerializer(employee, data=user_data)
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

        try:
            employee = Employee.objects.get(id=user_id)
            employee.user.delete()
            employee.delete()
            log_user_activity_task(request.tenant.name, 'Employee Deleted')
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

        tenant = request.tenant

        
        try:
            employee = authenticate(username=username, password=password)
            
            if not employee:
                return Response({"error": "Invalid credentials."},  
                                status=status.HTTP_404_NOT_FOUND)
            
            if not employee.is_active or not tenant.is_active:
                return Response({"error": "Your account  has been disabled."},
                                status=status.HTTP_403_FORBIDDEN)

            Employee.objects.get(user=employee)
            token_serializer = CustomEmployeeTokenObtainPairSerializer.get_token(employee)
            access_roken = token_serializer.access_token
            refresh_token = RefreshToken.for_user(employee)
            employee_instance = Employee.objects.get(user=employee)
            employee_serializer = UserListViewSerializer(employee_instance)


            return Response({"access_token": str(access_roken),
                            "refresh_token": str(refresh_token),
                             "profile": employee_serializer.data}, status=status.HTTP_200_OK)
        except Employee.DoesNotExist:

            return Response({"error": "invalid user"},
                            status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def user_access(request):
    try:

        users_id = request.data.get("user_ids")

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

    try:
        email = request.data.get("email")
        password = request.data.get("confirmPassword")
        old_password = request.data.get("oldPassword")
        tenant_name = request.tenant.name
        if not password:
            return Response({"error": "Password is required"},
                            status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({"error": "Email is required"},
                            status=status.HTTP_400_BAD_REQUEST)
        if not re.match(PASSWORD_REGEX,password):
            return Response({"error": "Password should be at least 8 characters long, and should containat "
            "least one uppercase letter, one lowercase letter, and one digit"},
                             status=status.HTTP_400_BAD_REQUEST)
        
        user=User.objects.get(username=email)
        if not user.check_password(old_password):
            return Response({"oldPassword": "Old password is incorrect."},
                            status=status.HTTP_400_BAD_REQUEST)
        if user.check_password(password):
            return Response({"error": "New password cannot be same as old password."},
                            status=status.HTTP_400_BAD_REQUEST)




        redis_key = f"password:{email}"
        redis_client.set(redis_key, json.dumps(password))
        redis_client.expire(redis_key, 1200)
        otp_data, expire = generate_otp(email)

        employee_password_change.delay(email, otp_data, tenant_name)

        return Response({"message": "OTP sent successfully"}, 
                        status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "Invalid user"},
                        status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:

        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def password_change_verify(request):

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
        "role": role,
        "contact_number":request.data.get("phone")
    }


    if not user_id:
        return Response({"error": "User ID is required"},
                        status=status.HTTP_400_BAD_REQUEST)
    if not profile_data:
        return Response({"error": "Profile Data is required"},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        if role == "owner":
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
                return Response(
                    {
                        "message": "Profile updated successfully"
                    }, status=status.HTTP_200_OK
                )
            else:

                return Response(
                    {"errors": serializer.errors
                     }, status=status.HTTP_400_BAD_REQUEST
                )
    
    except Exception as e:

        return Response({"error": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    try:
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"},status=status.HTTP_400_BAD_REQUEST)
        user=User.objects.get(username=email)
        if user and Tenant.objects.filter(email=email).exists():
            otp, expiry_minute = generate_otp(email)
            if otp:
                send_otp_email_task.delay(email,otp)
                return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)
@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password_employee(request):
    try:
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"},status=status.HTTP_400_BAD_REQUEST)
        user=User.objects.get(username=email)
        if user and Employee.objects.filter(user=user).exists():
            otp, expiry_minute = generate_otp(email)
            if otp:
                send_otp_email_task.delay(email,otp)
                return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password_verify_otp(request):
    try:
        email = request.data.get("email")
        otp = request.data.get("otp")
        if not email or not otp:
            return Response({"error": "Email and OTP are required"},status=status.HTTP_400_BAD_REQUEST)
        is_valid, message = validate_otp(email, otp)
        
        if not is_valid:
            return Response({"error": message}, 
                            status=status.HTTP_400_BAD_REQUEST)
        password = generate_password()
        user = User.objects.get(username=email)
        user.set_password(password)
        user.save()
        password_send.delay(email, password)
        return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)
    
        


class MyTokenObtainPairView(TokenObtainPairView):
    
    serializer_class = CustomEmployeeTokenObtainPairSerializer


class MyTokenRefreshView(TokenRefreshView):

    serializer_class = CustomRefreshSerializer


# ____________TEAM__________
     
class TeamManagmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        team_id = request.query_params.get("team_id")
        user_id = request.query_params.get("userId")

        try:
            if team_id:
                return self.get_team(request, team_id)

            if user_id:
                employee_ids = get_employee_and_subordinates_ids(user_id)
                teams = Team.objects.filter(team_lead__in=employee_ids)
            else:
                teams = Team.objects.all()

            serializer = TeamViewserilizer(teams, many=True)
            if serializer.data:
                return Response({"teams": serializer.data})
            return Response({"error": "No team found"})

        except Exception as e:

            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get_team(self, request, team_id):
        try:
            team = Team.objects.get(id=team_id)
            tasks = team.team_tasks.all()
            serializer = TeamViewserilizer(team)
            task_data = TaskViewSerializer(tasks,many=True)
            result = serializer.data.copy()
            result['tasks'] = task_data.data
            return Response({"team": result})
        except Team.DoesNotExist:
            return Response(
                {"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND
            )
       
    def post(self, request, *args, **kwargs):

        try:
            serializer = TeamSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Team created successfully","team":serializer.data},
                                status=status.HTTP_201_CREATED)
            return Response({"error": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, *args, **kwargs):

        team_id = request.data.get("team_id")

        try:
            
            team = Team.objects.get(id=team_id)
            serializer = TeamSerializer(team, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "message": "Successfully updated",
                        'team': serializer.data
                    }, status=status.HTTP_200_OK
                )

            return Response(
                {
                    "message": "Inavalid", "error": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:

            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    def patch(self, request, *args, **kwargs):
        team_id = request.data.get("team_id")
        try:
            team = Team.objects.get(id=team_id)
            serializer = TeamSerializer(team, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Team updated successfully","team":serializer.data},
                                status=status.HTTP_200_OK)
            return Response({"error": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request):
        team_id = request.data.get("team_id")
        try:
            

            team = Team.objects.get(id=team_id)
            team.delete()
            return Response({"message": "Sucessfully Deleted"}, status=status.HTTP_200_OK)
        except Team.DoesNotExist:
            return Response({"message": "Team is not Found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  

class TeamMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            team_id = request.query_params.get('team')

            team = Team.objects.get(id=team_id)
            team_members = team.team_members.all()
            employees = [member.employee for member in team_members]
            
            serializer = UserListViewSerializer(employees, many=True)
            if serializer.data:
                return Response({"team_member": serializer.data},
                                status=status.HTTP_200_OK)
             
            return Response({"error": "No team member found"},
                            status=status.HTTP_404_NOT_FOUND)
        
        except Team.DoesNotExist:
            return Response({"error": "Team not found"},
                            status=status.HTTP_404_NOT_FOUND)
        
    def post(self, request, *args, **kwargs):

        try:
            serializer = TeamMembersSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Team member created successfully"},
                                status=status.HTTP_201_CREATED)

            return Response({"error": serializer.errors}, 
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, *args, **kwargs):
        member_id = request.data.get("member_id")

        if not member_id:
            return Response({"error": "member_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            team_member = TeamMembers.objects.get(employee__id=member_id)
            team_member.delete()
            return Response({"message": "Team member removed successfully"}, status=status.HTTP_200_OK)
        except TeamMembers.DoesNotExist:
            return Response({"error": "Team member not found"}, status=status.HTTP_404_NOT_FOUND)


        



    


        

        
        

  
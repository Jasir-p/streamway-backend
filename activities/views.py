from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from tenant.pagination import StandardResultsSetPagination
from .models import Task,Email,Meeting
from .serializers import TaskSerializer, TaskViewSerializer,EmailSerializer,EmailsViewSerializer,MeetingSerializer,MeetingViewSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from users.models import Employee
from django.db.models import Subquery,Q
from datetime import datetime, timedelta
from django.utils import timezone
from tenant.utlis.get_tenant import get_schema_name
from communications.utlis.notification_handler import notification_set
from rest_framework.decorators import api_view,permission_classes
from Customer.models import Accounts,Contact
from Customer.serializers import ContactViewSerializer
from users.utlis.get_user import get_user
from users.utlis.employee_hierarchy import get_employee_and_subordinates_ids
from tenant.pagination import StandardResultsSetPagination
from tenant_panel.constants import FORBIDDEN_TITLE_CHARS_REGEX
from .filters import TaskFilter,EmailFilter,MeetingFilter



# Create your views here.

class TaskView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, *args, **kwargs):
        userid = request.query_params.get("assigned_to")

 

        try:
            task = Task.objects.all()
            task_filter = TaskFilter(request.GET, queryset=task)
            
            task = task_filter.qs
            if userid:
                employees = get_employee_and_subordinates_ids(userid)
                task =task.filter(assigned_to_employee__id__in=employees) 

            paginator = StandardResultsSetPagination()
            result_page = paginator.paginate_queryset(task, request)
            serializer = TaskViewSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, *args, **kwargs):

        try:           
            user_id = request.data.get("assigned_to_employee") 
            serializer = TaskSerializer(data=request.data)
            if serializer.is_valid():
                if request.data.get("assignTo") !="team":
                    user = Employee.objects.get(id=user_id)
                    notification_set(type="Task", message="Task Created",user=user)
                task_data=serializer.save()
                return Response(TaskViewSerializer(task_data).data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:

            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
        
    def patch(self, request, *args, **kwargs):
        try:
            task_id = request.query_params.get("task_id")
            task = Task.objects.get(id=task_id)
            serializer = TaskSerializer(task,data=request.data,partial=True)
            if serializer.is_valid():
                task_data=serializer.save()
                return Response(TaskViewSerializer(task_data).data, status=status.HTTP_200_OK)

            return Response({"message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        except Task.DoesNotExist:
            return Response({"message": "Task not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self,request):

        try:
            task_id = request.data.get("task_id")
            if not task_id:
                return Response({"message":"Id not found"}, status=status.HTTP_404_NOT_FOUND)
            task = Task.objects.get(id=task_id)
            if not task:
                return Response({"message":"task not found"}, status=status.HTTP_404_NOT_FOUND)
            
            task.delete()
            return Response({"message":"Deleted Successfully"}, status=status.HTTP_200_OK)
        
        except Exception as e:

            return Response ({"message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class TaskDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated] 


class EmailsView(APIView):
    permission_classes = [IsAuthenticated]
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class EmailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get("user_id")

        try:
            emails = Email.objects.all()

            
            email_filters = EmailFilter(request.query_params, queryset=emails)
            emails = email_filters.qs

            if user_id:
                employees_id = get_employee_and_subordinates_ids(user_id)
                emails = emails.filter(sender__id__in=employees_id)

            emails = emails.order_by("-sent_at")
            paginator = StandardResultsSetPagination()
            result_page = paginator.paginate_queryset(emails, request)
            serializer = EmailsViewSerializer(result_page, many=True)

            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            return Response(
                {"message": "Something went wrong", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        
    def post(self, request, *args, **kwargs):
        try:
            schema = get_schema_name(request)
            serializer = EmailSerializer(data=request.data,schema=schema)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_200_OK)

            return Response({"message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:

            return Response({"message":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class MeetingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get("userId")
        try:
            meetings = Meeting.objects.all()
            meeting_filters = MeetingFilter(request.GET, queryset=meetings)
            meetings = meeting_filters.qs

            if user_id:
                employees_ids = get_employee_and_subordinates_ids(user_id)
                meetings = meetings.filter(host__in=employees_ids)
            else:
                meetings = meetings.order_by("-id")
            serializer = MeetingViewSerializer(meetings, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": f"Error fetching data: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
    def post(self, request, *args, **kwargs):

        try:
            serializer = MeetingSerializer(data=request.data)
            user_id = request.data.get("host")
            if serializer.is_valid():
                
                user= get_user(user_id)
                notification_set(type="Meeting", message="Meeting Sheduled",user=user)
                meeting_data = serializer.save()
                return Response(MeetingViewSerializer(meeting_data).data,status=status.HTTP_200_OK)

            return Response({"message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:

            return Response({"message":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def patch( self, request, *args, **kwargs):
        try:

            meeting_id = kwargs.get('meeting_id')
            user_id = request.data.get("host")

            meeting = Meeting.objects.get(id=meeting_id)
            serializer = MeetingSerializer(meeting, data=request.data, partial=True)
            if serializer.is_valid():
                if user_id:
                    user= get_user(user_id)
                    notification_set(type="Meeting", message="Meeting Sheduled",user=user)
                meeting_data = serializer.save()
                return Response(MeetingViewSerializer(meeting_data).data,status=status.HTTP_200_OK)
            return Response({"message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:

            return Response({"message":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete( self, request, *args, **kwargs):
        try:
            meeting_id = kwargs.get('meeting_id')
            meeting = Meeting.objects.get(id=meeting_id)
            meeting.delete()
            return Response({"message": "Meeting deleted successfully"}, status=status.HTTP_200_OK)
        
        except Exception as e:

            return Response({"message":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_contacts_by_account(request,*args, **kwargs):
    try:
        account_id = kwargs.get('account_id')
        conatcts = Contact.objects.filter(account_id__id=account_id)
        serializer = ContactViewSerializer(conatcts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({"message": f"Error fetching data: {str(e)}"}, status=status.HTTP_404_NOT_FOUND)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from tenant.pagination import StandardResultsSetPagination
from .models import Task,Email
from .serializers import TaskSerializer, TaskViewSerializer,EmailSerializer,EmailsViewSerializer
from django.contrib.contenttypes.models import ContentType
from tenant.utlis.get_tenant import get_schema_name
from django_tenants.utils import schema_context
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import RetrieveUpdateDestroyAPIView
import stripe
from users.models import Employee
from django.db.models import Subquery,Q
from datetime import datetime, timedelta
from django.utils import timezone
from tenant.utlis.get_tenant import get_schema_name


# Create your views here.

class TaskView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, *args, **kwargs):
        print(datetime.now())
        print(timedelta(days=30))
        now = timezone.now()
        print("checktime",now)
        userid = request.query_params.get("assigned_to")
        print(userid)
 

        try:
            if userid:
                employees = Employee.objects.filter(
                    Q(id=userid) | Q(role__parent_role=Subquery(Employee.objects.filter(id=userid).values("role")[:1]))
                ).values_list("id", flat=True)

                task =Task.objects.filter(assigned_to_employee__id__in=employees) 
            else:
                task = Task.objects.all()
            serializer = TaskViewSerializer(task, many=True, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request, *args, **kwargs):
        print(request.data)
        try:
            serializer = TaskSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
        
    def put(self, request, *args, **kwargs):
        try:
            task_id = request.data .get('id')
            task = Task.objects.get(id=task_id)
            serializer = TaskSerializer(task,data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({serializer.data}, status=status.HTTP_200_OK)
            return Response({"message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self,request):
        print(request.data.get("task_id"))
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
            print(str(e))
            return Response ({"message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class TaskDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated] 


class EmailsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            emails = Email.objects.all()
            serializer = EmailsViewSerializer(emails, many=True)
            if serializer.data:
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"message":"No data found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request, *args, **kwargs):
        try:
            print(request.data)
            schema = get_schema_name(request)
            serializer = EmailSerializer(data=request.data,schema=schema)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_200_OK)
            print(serializer.errors)
            return Response({"message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(str(e))
            return Response({"message":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




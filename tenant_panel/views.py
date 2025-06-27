from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from leads.models import Leads,Deal
from users.utlis.employee_hierarchy import get_employee_and_subordinates_ids
from activities.models import Task,Meeting
from leads.serializers import LeadsGetSerializer,DealsViewserializer
from activities.serializers import TaskViewSerializer,MeetingViewSerializer



# Create your views here.

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tenant_dashboard_content(request):
    user_id = request.query_params.get("userId")

    if user_id:
        employees_id = get_employee_and_subordinates_ids(user_id)
        leads = Leads.objects.filter(employee__in=employees_id).order_by('-created_at')
        deals = Deal.objects.filter(owner__in=employees_id).order_by('-created_at')
        tasks = Task.objects.filter(assigned_to_employee__in=employees_id).order_by('-created_at')
        meetings = Meeting.objects.filter(host__in=employees_id).order_by('-created_at')
    else:
        leads = Leads.objects.all().order_by('-created_at')
        deals = Deal.objects.all().order_by('-created_at')
        tasks = Task.objects.all().order_by('-created_at')
        meetings = Meeting.objects.all().order_by('-created_at')
    
    return Response({
        'leads': LeadsGetSerializer(leads,many=True).data,
        'deals': DealsViewserializer(deals, many=True).data, 
        'tasks': TaskViewSerializer(tasks, many=True).data,
        'meetings':MeetingViewSerializer(meetings, many=True).data,
        })


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def get_tenant_analytics(request):
#     user_id = request.query_params.get("userId")
#     if user_id:






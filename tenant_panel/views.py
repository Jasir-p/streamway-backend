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
from tenant_panel.services import get_analytics,get_teams_analytics,get_tenants_analytics
from users.models import Employee,Team
import logging
import json
from .utils.filters import parse_filter_params

logger = logging.getLogger(__name__)


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_employee_analytics(request):
    try:
        user_id = request.query_params.get("userId")
        filter_item = request.query_params.get("filter")
        filter_info = parse_filter_params(filter_item)
        filter_type = filter_info['filter_type']
        start_date = filter_info['start_date']
        end_date = filter_info['end_date']


    
        data = []

        if user_id:
            employee_ids = get_employee_and_subordinates_ids(user_id)
            for eid in employee_ids:
                    try:
                        emp_analytics = get_analytics(eid,filter_type,start_date, end_date)
                        data.append(emp_analytics)
                    except Exception as e:
                        logger.error(f"Analytics error for employee {eid}: {str(e)}")
            
            
        else:
            employee_ids = Employee.objects.all().values_list('id', flat=True)
            for emp_id in employee_ids:
                    try:
                        response = get_analytics(emp_id,filter_type,start_date, end_date)
                        data.append(response)
                    except Exception as e:
                        logger.error(f"Analytics error for employee {emp_id}: {str(e)}")

        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in get_employee_analytics: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_team_analytics(request):
    try:
        data = []
        
        filter_item = request.query_params.get("filter")
        filter_info = parse_filter_params(filter_item)
        filter_type = filter_info['filter_type']
        start_date = filter_info['start_date']
        end_date = filter_info['end_date']
        teams = Team.objects.all()

        if not teams.exists():
            return Response({"error": "No teams found."}, status=status.HTTP_404_NOT_FOUND)

        for team in teams:
            try:
                team_analytics = get_teams_analytics(team,filter_type,start_date,end_date)
                data.append(team_analytics)
            except Exception as inner_error:

                continue  

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Unexpected error in get_team_analytics: {str(e)}")
        return Response({"error": "Something went wrong while fetching team analytics."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_tenant_analytics(request):
    try:
        filter_item = request.query_params.get("filter")
        filter_info = parse_filter_params(filter_item)
        filter_type = filter_info['filter_type']
        start_date = filter_info['start_date']
        end_date = filter_info['end_date']
        tenant_analytics = get_tenants_analytics(filter_type,start_date,end_date)
        return Response(tenant_analytics, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error in get_tenant_analytics: {str(e)}")
        return Response({"error": "Something went wrong while fetching tenant analytics."},
                         status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        



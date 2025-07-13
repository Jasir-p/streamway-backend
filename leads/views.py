
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import LeadFormField, Leads,WebForm,LeadNotes,Deal,DealNotes
from rest_framework.permissions import IsAuthenticated,AllowAny
from leads.serializers import( LeadFormSerializers, 
                              LeadSerializers,WebformSerializer, 
                              LeadsGetSerializer, 
                              WebformListViewSerializer,
                              LeadAssignSerializer,
                              LeadNoteViewSerializer,
                              LeadNoteSerializer,
                              DealsSerializer,
                              DealsViewserializer,
                              DealNotesSerializer,
                              DealNotesViewSerializer)

from rest_framework import status
from tenant.pagination import StandardResultsSetPagination 
from users.models import Employee
from rest_framework.decorators import api_view, permission_classes
from users.serializer import UserListViewSerializer
from django.db.models import Exists, OuterRef, Subquery,Q,When,BooleanField,Case,Value
from django.shortcuts import get_object_or_404
from tenant.utlis.get_tenant import get_schema_name
from Customer.serializers import ContactSerializer,AccountsSerilalizer
from activities.serializers import TaskViewSerializer
from users.utlis.employee_hierarchy import get_employee_and_subordinates_ids
from .services import get_deal_status_summary,get_lead_status_summary
from django.utils import timezone
from tenant_panel.utils.filters import  parse_filter_params
from tenant_panel.utils.applay_date_filter import apply_date_filter
from communications.utlis.notification_handler import notification_set

import logging

logger = logging.getLogger(__name__)



class FormfieldView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        formfields = LeadFormField.objects.all()
        serializer = LeadFormSerializers(formfields, many=True)
        return Response({'formfields': serializer.data})
    
    def post(self, request, *args, **kwargs):
        
        if request.data:
            serializer = LeadFormSerializers(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Form saved successfully'},
                                status=status.HTTP_201_CREATED)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        
    def put(self, request):
        try:
            field_id = request.data.get('field_id')
            field = LeadFormField.objects.get(id=field_id)
            serializer = LeadFormSerializers(field, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Form updated successfully'},
                                status=status.HTTP_200_OK)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
                    
    def delete(self, request):
        field_id = request.data.get('field_id')
        if not field_id:
            return Response({'message': 'Please provide field id'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            field = LeadFormField.objects.get(id=field_id)
            field.delete()
            return Response({'message': 'Field deleted successfully'},
                            status=status.HTTP_200_OK)
        except LeadFormField.DoesNotExist:
            return Response({'message': 'Field does not exist'},
                            status=status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
@permission_classes([AllowAny])
def get_form_fields(request):
    formfields = LeadFormField.objects.all()
    serializer = LeadFormSerializers(formfields, many=True)
    return Response({'formfields': serializer.data})

        
class LeadsView(APIView):
    
    permission_classes = [IsAuthenticated]
    def get(self, request):
        userid = request.query_params.get("userId")
        
        try:
            if userid:
                employees = get_employee_and_subordinates_ids(userid)
                leads = Leads.objects.filter(employee__in=employees).order_by("-created_at")

            else:
                leads = Leads.objects.all().order_by("-created_at")

            paginator = StandardResultsSetPagination()
            result_page = paginator.paginate_queryset(leads, request)
            serializer = LeadsGetSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

    def post(self, request, *args, **kwargs):
        schema = get_schema_name(request)
        if request.data:
            serializer = LeadSerializers(data=request.data, schema=schema)
            if serializer.is_valid():
                instance = serializer.save()
                response_data = LeadSerializers(instance, schema=schema).data
                return Response(
                    {
                        'message': 'Lead saved successfully',
                        'data': response_data
                    },
                    status=status.HTTP_201_CREATED
                )
            else:
                logger.error(f"adding error for lead section: {str(serializer.errors)}")
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            
            return Response(
                {'message': 'No data provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    def patch(self, request, *args, **kwargs):
        
        lead_id = request.data.get("lead_id")
        lead = get_object_or_404(Leads, lead_id=lead_id)
        serilaizer = LeadSerializers(lead, data=request.data, partial=True)
        if serilaizer.is_valid():
            serilaizer.save()
            return Response(
              {'message': 'Lead updated successfully','lead':serilaizer.data},
              status=status.HTTP_200_OK
            )
        return Response(serilaizer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, *args, **kwargs):
        try:
            leads_id = request.data.get('lead_id')
            if isinstance(leads_id, int):
                leads_id = [leads_id]
            if not leads_id:
                return Response(
                    {'message': 'No leads id provided'},
                    status=status.HTTP_400_BAD_REQUEST
                ) 
            leads = Leads.objects.filter(lead_id__in=leads_id)
            leads.delete()
            return Response(    
                {'message': 'Leads deleted successfully'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
             )
     

@api_view(["GET"])
@permission_classes([IsAuthenticated])  
def lead_overview(request):
    try:
        lead_id = request.query_params.get("lead_id")
        Lead = Leads.objects.get(lead_id=lead_id)
        lead_notes = LeadNotes.objects.filter(lead__lead_id=lead_id).order_by('-created_at')
        serializer = LeadsGetSerializer(Lead)
        task_count = Lead.tasks.all()
        response_data = serializer.data.copy()
        response_data['notes'] = LeadNoteViewSerializer(lead_notes, many=True).data
        response_data['tasks'] = TaskViewSerializer(task_count, many=True).data

        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

class LeadNotesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            lead_id = request.GET.get("lead_id")
            notes = LeadNotes.objects.filter(lead_id=lead_id).order_by("-created_at")
            serializer = LeadNoteViewSerializer(notes, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request, *args, **kwargs):
        try:
            serializer = LeadNoteSerializer(data=request.data)           
            if serializer.is_valid():                
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_employee(request):
    
    try:
        role = request.query_params.get("role")
        if role == "owner" and role:
            employees = Employee.objects.all()
        else:

            user_id = request.query_params.get("user_id")
            employee = Employee.objects.get(id=user_id)
            employees = Employee.objects.filter(
                role__parent_role=employee.role
            )
        serializer = UserListViewSerializer(employees, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    
class WebEnquiry(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, *args, **kwargs):
        try:
            enquiry_data = WebForm.objects.annotate(
                employee=Subquery(
                    Leads.objects.filter(
                        form_data=OuterRef("pk")
                     ).values("employee")[:1]
                  ), granted_by=Subquery(
                    Leads.objects.filter(form_data=OuterRef("pk")
                     ).values("granted_by")[:1]),
                lead_created=Case(
                        When(Exists(Leads.objects.filter(form_data=OuterRef("pk"))), then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ).order_by("-created_at")
            
            serializer = WebformListViewSerializer(enquiry_data, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        
    def post(self, request, *args, **kwargs):
        try:
            serializer = WebformSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                notification_set(type="Enquiry", message="New Enquiry",user=None)
                
                return Response(
                    {'message': 'Enquiry submitted'}, status=status.HTTP_200_OK
                )
            else:
                logger.error(serializer.errors)
                return Response(
                    {"detail":"Invalid input", "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        
    def delete(self, request, *args, **kwargs):
        try:
            enquiry_id = request.data.get("enquiryIds")
            if isinstance(enquiry_id, str):
                enquiry_id = [enquiry_id]
            if not enquiry_id:
                return Response(
                 {'error': 'No enquiry id provided'},
                 status=status.HTTP_400_BAD_REQUEST
                )
            enquiry = WebForm.objects.filter(web_id__in=enquiry_id)
            
            enquiry.delete()
            return Response(
                
                {'message': 'Enquiry deleted'}, status=status.HTTP_200_OK
            
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        
        
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def lead_assign(request):
    try:
        serializer = LeadAssignSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Lead assigned'}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def status_update(request):
    try:
        status_label = request.data.get("status")
        lead_ids = request.data.get("lead_id")
        if not status or not lead_ids:
            return Response(
                {'error': 'Status and lead id are required'},

                status=status.HTTP_400_BAD_REQUEST
            )
        if not isinstance(lead_ids, list):
            lead_ids = [lead_ids]
        valid_status = [choice[0] for choice in Leads.STATUS_CHOICES]
        if status_label not in valid_status:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        lead = Leads.objects.filter(lead_id__in=lead_ids)
        if not lead.exists():
            return Response({'error': 'Lead not found'}, status=status.HTTP_400_BAD_REQUEST)
        lead.update(status=status_label)
        return Response(
            {'message': 'Status updated'}, status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def convert_to(request):
    try:
        lead_id = request.data.get("lead")
        customer = request.data.get("convert_to_customer")

        if not lead_id:
            return Response({'error': 'Lead id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if  not customer:
            return Response({'error': 'Either customer is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = {}

        customer_serializer = AccountsSerilalizer(data=request.data)
        if customer_serializer.is_valid():
            customer_serializer.save()
            result['customer'] = customer_serializer.data
        else:
            return Response(
                {"error": customer_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            
            {
                'message': 'Lead converted successfully', 
                'data': result}, status=status.HTTP_200_OK
                )
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DealView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        userid = request.query_params.get("userId")
        try:
            if userid:
                employees =get_employee_and_subordinates_ids(userid)
                Deals = Deal.objects.filter(owner__in=employees).order_by("-created_at")

            else:
                Deals = Deal.objects.all().order_by("-created_at")
                
            paginator = StandardResultsSetPagination()
            result_page = paginator.paginate_queryset(Deals, request)
            serializer = DealsViewserializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        try:
            deal_serializer = DealsSerializer(data=request.data)
            if deal_serializer.is_valid():
                deal_view= deal_serializer.save()
                
                return Response({'message': 'Deal created successfully', 'data': DealsViewserializer(deal_view).data}, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': deal_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, *args, **kwargs):
        try:
            deal_id = request.data.get("deal_id")
            
            if not deal_id:
                return Response(
                    {'error': 'Deal ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                deal = Deal.objects.get(deal_id=deal_id)
            except Deal.DoesNotExist:
                return Response(
                    {'error': 'Deal not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            deal_serializer = DealsSerializer(deal, data=request.data, partial=False)
            if deal_serializer.is_valid():
                updated_deal = deal_serializer.save()
                
                return Response({
                    'message': 'Deal updated successfully',
                    'data': DealsViewserializer(updated_deal).data
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': deal_serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def patch(self, request, *args, **kwargs):
            try:
                deal_ids = request.data.get('deal_ids', [])
                updates = request.data.get('updates', {})

                if not deal_ids:
                    return Response(
                        {'error': 'No deal IDs provided'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if not updates:
                    return Response(
                        {'error': 'No updates provided'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                deals = Deal.objects.filter(deal_id__in=deal_ids)

                if not deals.exists():
                    return Response(
                        {'error': 'No valid deals found for provided IDs'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                updated_deals = []
                for deal in deals:
                    for key, value in updates.items():
                        if hasattr(deal, key):
                            setattr(deal, key, value)
                    deal.save()
                    updated_deals.append(deal)

                serializer = DealsViewserializer(updated_deals, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)

            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    def delete(self, request, *args, **kwargs):
        try:
            deal_ids = request.data.get('deal_ids', [])
            deals = Deal.objects.filter(deal_id__in=deal_ids)
            if not deals.exists():
                return Response({'error': 'No valid deals found for provided IDs'}, 
                                status=status.HTTP_404_NOT_FOUND)
            deals.delete()
            return Response({'message': 'Deals deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


            
        
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_deal_overview(request,*args, **kwargs):
    deal_id = request.query_params.get("dealId")
    if not deal_id:
        return Response({'error': 'No deal ID provided'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        deal = Deal.objects.get(deal_id=deal_id)
        deal_notes = deal.notes.all().order_by('-created_at')
        deal_contact = deal.account_id.contacts.filter(is_primary_contact=True).first()
        serializer = DealsViewserializer(deal)
        response_data = serializer.data.copy()
        response_data['dealContact'] = ContactSerializer(deal_contact).data if deal_contact else {}
        response_data['dealNotes'] = DealNotesViewSerializer(deal_notes, many=True).data
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


class DealNoteView (APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            serializer = DealNotesSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_pipeline(request, *args, **kwargs):
    user_id = request.query_params.get("userId")
    filter_items = request.query_params.get("filter")
    try:
        filter_info = parse_filter_params(filter_items)
        filter_type = filter_info['filter_type']
        start_date = filter_info['start_date']
        end_date = filter_info['end_date']

        if user_id:
            employee_ids = get_employee_and_subordinates_ids(user_id)
            leads = Leads.objects.filter(employee__in=employee_ids).order_by("-created_at")

            deals = Deal.objects.filter(owner__in=employee_ids).order_by("-created_at")


            lead_status_summary = get_lead_status_summary(filter_type, start_date, end_date,employee_ids)
            deal_status_summary = get_deal_status_summary(filter_type, start_date, end_date,employee_ids)
        else:
            leads = Leads.objects.all().order_by("-created_at")
            deals = Deal.objects.all().order_by("-created_at")


            lead_status_summary = get_lead_status_summary(filter_type, start_date, end_date)
            deal_status_summary = get_deal_status_summary(filter_type, start_date, end_date)
        
        
        latest_leads = LeadsGetSerializer(leads[:5], many=True).data
        latest_deals = DealsViewserializer(deals[:5], many=True).data

        data = {
            "latest_leads": latest_leads,
            "latest_deals": latest_deals,
            "lead_status_summary": list(lead_status_summary),
            "deal_status_summary": list(deal_status_summary),
        }

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:

        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






        




from rest_framework.views import APIView
from rest_framework.response import Response
from .models import LeadFormField, Leads,WebForm,LeadNotes
from rest_framework.permissions import IsAuthenticated
from leads.serializers import( LeadFormSerializers, 
                              LeadSerializers,WebformSerializer, 
                              LeadsGetSerializer, 
                              WebformListViewSerializer,
                              LeadAssignSerializer,
                              LeadNoteViewSerializer,
                              LeadNoteSerializer)
from rest_framework import status
from tenant.pagination import StandardResultsSetPagination 
from users.models import Employee
from rest_framework.decorators import api_view, permission_classes
from users.serializer import UserListViewSerializer
from django.db.models import Exists, OuterRef, Subquery,Q,When,BooleanField,Case,Value
from django.shortcuts import get_object_or_404
from tenant.utlis.get_tenant import get_schema_name
from Customer.serializers import ContactSerializer,AccountsSerilalizer



class FormfieldView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        formfields = LeadFormField.objects.all()
        serializer = LeadFormSerializers(formfields, many=True)
        print(serializer.data)
        return Response({'formfields': serializer.data})
    
    def post(self, request, *args, **kwargs):
        
        if request.data:
            print(request.data)
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
        print(field_id)
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
        
        
class LeadsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        userid = request.query_params.get("userId")
        print(userid)
        
        try:
            if userid:
                employees = Employee.objects.filter(
                    Q(id=userid) | Q(role__parent_role=Subquery(Employee.objects.filter(id=userid).values("role")[:1]))
                ).values_list("id", flat=True)
                leads = Leads.objects.filter(employee__in=employees).order_by("-created_at")

            else:
                leads = Leads.objects.all().order_by("-created_at")
                
            paginator = StandardResultsSetPagination()
            result_page = paginator.paginate_queryset(leads, request)
            serializer = LeadsGetSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            print(str(e))
            return Response(
                
                {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
            
            )

    def post(self, request, *args, **kwargs):
        tenant = request.tenant
        schema = get_schema_name(request)
        print(schema)
        if request.data:
            print(request.data)
            serializer = LeadSerializers(data=request.data, schema=schema)
            if serializer.is_valid():
                
                response = serializer.save()
                print(response)
                return Response(
                    {'message': 'Lead saved successfully'},
                    status=status.HTTP_201_CREATED
                )
            else:
                print(serializer.errors)
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
        print(request.data)
        
        lead_id = request.data.get("lead_id")
        print(lead_id)
        lead = get_object_or_404(Leads, lead_id=lead_id)
        serilaizer = LeadSerializers(lead, data=request.data, partial=True)
        if serilaizer.is_valid():
            serilaizer.save()
            return Response(
              {'message': 'Lead updated successfully','lead':serilaizer.data},
              status=status.HTTP_200_OK
            )
        print(serilaizer.errors)
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
            print(leads)
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
        note = LeadNoteViewSerializer(lead_notes, many=True)
        response_data = serializer.data.copy()
        response_data['notes'] = note.data

        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    



# class LeadAsignView(APIView):

#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         try:
#             user_id = request.data.get("user_id")
#             employee = Employee.objects.get(id=user_id)
#             print(employee)
#             employees = list(Employee.objects.filter(role__parent_role=employee.role).values_list("id", flat=True))

#             print("emp", employees)
#             employees.append(user_id)
#             print("emp", employees)
#             leads_asign = LeadAcess.objects.filter(employee__id__in=employees)
#             print(leads_asign)
#             serializer = LeadAcessGetSerializer(leads_asign, many=True)
#             print(serializer.data)
#             return Response(serializer.data)
#         except Exception as e:
#             print(str(e))
#             return Response(
                
#                 {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
#             )
        
#     def post(self, request, *args, **kwargs):
#         print(request.data)
#         try:
#             serializer = LeadAssignSerializer(data=request.data)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(
#                     serializer.data, status=status.HTTP_201_CREATED
#                 )
#             print(serializer.errors)
#             return Response(
#                 serializer.errors, status=status.HTTP_400_BAD_REQUEST
#             )
#         except Exception as e:
#             print(str(e))
#             return Response(
#                 {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
#             )
#     def delete(self, request, *args, **kwargs):
#         try:
#             lead_id = request.data.get("lead_id")
#             LeadAcess.objects.filter(lead_id=lead_id).delete()
#             return Response({'message': 'Lead deleted'}, status=status.HTTP_200_OK)
#         except Exception as e:
#             print(str(e))
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LeadNotesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        try:
            lead_id = request.GET.get("lead_id")
            notes = LeadNotes.objects.filter(lead_id=lead_id).order_by("-created_at")
            serializer = LeadNoteViewSerializer(notes, many=True)
            return Response(serializer.data)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request, *args, **kwargs):
        try:
            print(request.data)
            serializer = LeadNoteSerializer(data=request.data)
            
            if serializer.is_valid():
                
                serializer.save()
                print(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_employee(request):
    
    try:
        role = request.query_params.get("role")
        print(role)
        if role == "owner" and role:
            employees = Employee.objects.all()
        else:

            user_id = request.query_params.get("user_id")
            print(user_id)
            employee = Employee.objects.get(id=user_id)
            print(employee)
            employees = Employee.objects.filter(
                role__parent_role=employee.role
            )
        serializer = UserListViewSerializer(employees, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(str(e))
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    
class WebEnquiry(APIView):
    permission_classes = [IsAuthenticated]

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
            print(str(e))
            return Response(
                {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        
    def post(self, request, *args, **kwargs):
        try:
            serializer = WebformSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {'message': 'Enquiry submitted'}, status=status.HTTP_200_OK
                )
            else:
                print(serializer.errors)
                return Response(
                    {"detail":"Invalid input", "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            print(str(e))
            return Response(
                {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        
    def delete(self, request, *args, **kwargs):
        try:
            enquiry_id = request.data.get("enquiryIds")
            print(enquiry_id)
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
            print(str(e))
            return Response(
                {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        
        
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def lead_assign(request):
    print(request.data)
    try:
        serializer = LeadAssignSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Lead assigned'}, status=status.HTTP_200_OK
            )
        print("theline", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   
    except Exception as e:
        print(str(e))

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
        print(status_label)
        print(valid_status)
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
        print(str(e))
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def convert_to(request):
    try:
        lead_id = request.data.get("lead")
        contact = request.data.get("convert_to_contact")
        customer = request.data.get("convert_to_customer")

        if not lead_id:
            return Response({'error': 'Lead id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not contact and not customer:
            return Response({'error': 'Either contact or customer is required'}, status=status.HTTP_400_BAD_REQUEST)
        result = {}
        if contact:
            contact_serializer = ContactSerializer(data=request.data)
            if contact_serializer.is_valid():
                contact_serializer.save()
                result['contact'] = contact_serializer.data
            else:
                return Response(
                    {"error": contact_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST

                )
        if customer:
            print("haii")
            customer_serializer = AccountsSerilalizer(data=request.data)
            if customer_serializer.is_valid():
                customer_serializer.save()
                result['customer'] = customer_serializer.data
            else:
                print(customer_serializer.errors)
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
        print(str(e))
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

        


                       
    
        





        


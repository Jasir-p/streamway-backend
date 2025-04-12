

from rest_framework.views import APIView
from rest_framework.response import Response
from .models import LeadFormField, Leads,WebForm
from rest_framework.permissions import IsAuthenticated
from leads.serializers import LeadFormSerializers, LeadSerializers,WebformSerializer, LeadsGetSerializer, WebformListViewSerializer,LeadAssignSerializer
from rest_framework import status
from tenant.pagination import StandardResultsSetPagination 
from users.models import Employee
from rest_framework.decorators import api_view, permission_classes
from users.serializer import UserListViewSerializer
from django.db.models import Exists, OuterRef, Subquery,Q,When,BooleanField,Case,Value
from django.shortcuts import get_object_or_404
from tenant.utlis.get_tenant import get_schema_name


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


class LeadsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        userid = request.query_params.get("userId")
        print(userid)
        print(get_schema_name(request))
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
        print(tenant)
        if request.data:
            print(request.data)
            serializer = LeadSerializers(data=request.data)
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
        
        lead_id = request.data.get("lead_id")
        print(lead_id)
        lead = get_object_or_404(Leads, lead_id=lead_id)
        serilaizer = LeadSerializers(lead, data=request.data, partial=True)
        if serilaizer.is_valid():
            serilaizer.save()
            return Response(
              {'message': 'Lead updated successfully'},
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
                return Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
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







    
        





        


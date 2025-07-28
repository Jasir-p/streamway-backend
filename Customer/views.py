
from .models import Contact, Accounts,Notes
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import( 
    ContactSerializer, 
    ContactViewSerializer, 
    AccountsSerilalizer, 
    AccountsViewSerializer, 
    ContactsAsssignSerializer, 
    AccountCustomizedSerializer,
    AccountNotesSerializer,
    AccountNoteViewSerializer,
    AccountAssignSerializer)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from tenant.pagination import StandardResultsSetPagination
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from activities.serializers import TaskViewSerializer
from leads.serializers import DealsViewserializer
from .filters import AccountFilter,ContactFilter
from users.utlis.employee_hierarchy import get_employee_and_subordinates_ids

class ContactView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        userid = request.query_params.get("user_id")
        try:


            contacts = Contact.objects.all()
            contact_filter = ContactFilter(request.GET, queryset=contacts)
            contacts = contact_filter.qs
            if userid:
                employees = get_employee_and_subordinates_ids(userid)
                contacts = contacts.filter(assigned_to__id__in=employees)
            
            pagination = StandardResultsSetPagination()
            result_page = pagination.paginate_queryset(contacts, request)
            serializer = ContactViewSerializer(result_page, many=True)

            return pagination.get_paginated_response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
            
    def post(self, request, *args, **kwargs):

        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Contact created","contact":serializer.data}, status=status.HTTP_201_CREATED
            )

        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request, *args, **kwargs):
        contact_id = request.query_params.get("contact_id")
        if not contact_id:
            return Response({"error": "Missing contact_id in query parameters"}, status=status.HTTP_400_BAD_REQUEST)

        contact = get_object_or_404(Contact, pk=contact_id)
        serializer = ContactSerializer(contact, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Contact updated", "contact": ContactViewSerializer(serializer.instance).data}, status=status.HTTP_200_OK)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                                

        
    def delete(self, request, *args, **kwargs):
        try:
            contact_ids = request.data.get("contact_ids")

            contacts = Contact.objects.filter(id__in=contact_ids)
            contacts.delete()
            return Response(
                
                {"message": "Contact deleted"}, status=status.HTTP_200_OK
            
            )
        except Exception as e:

            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


class AccountsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):

        userid = request.query_params.get("user_id")
        try:
            accounts = Accounts.objects.all()
            filter_accounts = AccountFilter(request.GET,queryset =accounts )
            accounts = filter_accounts.qs
            
            if userid:
                 employees = get_employee_and_subordinates_ids(userid)
                 accounts = accounts.filter(assigned_to__id__in=employees)

            pagination = StandardResultsSetPagination()
            result_page = pagination.paginate_queryset(accounts, request)
            serializer = AccountsViewSerializer(result_page, many=True)
            return pagination.get_paginated_response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request):
        serializer = AccountsSerilalizer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Account created"}, status=status.HTTP_201_CREATED)
        else:
            
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    def patch(self, request):
        account_id = request.query_params.get("account_id")
        if not account_id:
            return Response({"message": "Account ID not provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            account = Accounts.objects.get(id=account_id)
        except Accounts.DoesNotExist:
            return Response({"message": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = AccountsSerilalizer(account, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(AccountsViewSerializer(serializer.instance).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
    def delete(self, request):
        try:
            account_ids = request.data.get("account_ids")
            accounts = Accounts.objects.filter(id__in=account_ids)
            accounts.delete()
            return Response({"message": "Account deleted"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def assign_to_contact(request):

    try:
        serializer = ContactsAsssignSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'contact assigned'}, status=status.HTTP_200_OK
            )
        return Response({'message':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:

        return Response({"error":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def account_overview(request):
    account_id = request.query_params.get("account_id")
    if not account_id:
        return Response({"detail": "Account ID is required."}, status=400)
    account = get_object_or_404(Accounts, id=account_id)
    notes = Notes.objects.filter(account__id=account_id)
    serializer = AccountsViewSerializer(account)
    serializer_note = AccountNoteViewSerializer(notes, many=True)
    task_count = account.tasks.all()
    task_data = TaskViewSerializer(task_count, many=True)
    contacts = account.contacts.all()
    deals= account.deals.all()
    

    response_data = serializer.data.copy()  # Convert to mutable dictionary
    response_data['notes'] = serializer_note.data
    response_data["tasks"]=task_data.data
    response_data["contacts"]= ContactViewSerializer(contacts, many=True).data
    response_data["deals"]=DealsViewserializer(deals, many=True).data

    return Response(response_data)



class AccountCustomisedView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):

        account_id = request.query_params.get("account_id")
        if not account_id:
            return Response({"detail": "Account ID is required."}, status=400)

        account = Accounts.objects.filter(id=account_id).first()
        if not account:
            return Response({"detail": "Account not found."}, status=404)


        key = request.data.get("key")
        value = request.data.get("value")
        is_editing = request.data.get("is_Editing")
        new_key = request.data.get("name")


        if "key" in request.data:

            if not is_editing:
                if account.custome_fields is None :
                    account.custome_fields = {}
                if key in account.custome_fields:
                        return Response(
                            {"detail": f"Field '{key}' already exists in custom fields."},
                            status=400
                        )
                
                account.custome_fields[key] = value
            else:
                if key in account.custome_fields:
                    account.custome_fields[new_key]= account.custome_fields.pop(key)
                    account.custome_fields[new_key]= value

            account.save()
            return Response(AccountCustomizedSerializer(account).data, status=200)

        serializer = AccountCustomizedSerializer(account, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)


        return Response(serializer.errors, status=400)

    def delete(self,request):

        account_id = request.query_params.get("account_id")
        if not account_id:
            return Response({"detail": "Account ID is required."}, status=400)

        account = Accounts.objects.filter(id=account_id).first()
        if not account:
            return Response({"detail": "Account not found."}, status=404)
        
        key = request.data.get("key")
        if key in account.custome_fields:
            removed = account.custome_fields.pop(key)
            account.save()
            return Response({"message":"Removed SUccessfully","field":removed}, status=status.HTTP_200_OK)
        return Response({"message":"error occured"}, status=status.HTTP_400_BAD_REQUEST)


class AccountsNotesView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        notes = Notes.objects.all()
        serializer =AccountNoteViewSerializer(notes, many=True)
        return Response(serializer.data)
        

    def post(self,request, *args, **kwargs):
        serializer = AccountNotesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response ({"message":"successfully Added"}, status=status.HTTP_201_CREATED)
        
        return Response({"message":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete (self,request, *args, **kwargs):
        note_id = request.data.get("note_id")
        if not note_id:
            return Response({"detail": "Note ID is required."}, status=400)
        Notes.objects.get(id=note_id).delete()
        return Response({"message":"Note Deleted Successfully"}, status=status.HTTP_200_OK)
    

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def assign_to_account(request):
    try:
        serializer= AccountAssignSerializer(data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Account assigned successfully"}, status=status.HTTP_200_OK)
        return Response({"message":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"message":str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    

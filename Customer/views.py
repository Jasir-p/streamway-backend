
from .models import Contact, Accounts
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ContactSerializer, ContactViewSerializer, AccountsSerilalizer, AccountsViewSerializer, ContactsAsssignSerializer, AccountCustomizedSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from tenant.pagination import StandardResultsSetPagination
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404


class ContactView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:

            contacts = Contact.objects.all()
            
            pagination = StandardResultsSetPagination()
            result_page = pagination.paginate_queryset(contacts, request)
            serializer = ContactViewSerializer(result_page, many=True)

            return pagination.get_paginated_response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
            
    def post(self, request, *args, **kwargs):
        print(request.data)
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Contact created","contact":serializer.data}, status=status.HTTP_201_CREATED
            )
        print(serializer.errors)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        
    def delete(self, request, *args, **kwargs):
        try:
            contact_ids = request.data.get("contact_ids")
            print(contact_ids)
            contacts = Contact.objects.filter(id__in=contact_ids)
            contacts.delete()
            return Response(
                
                {"message": "Contact deleted"}, status=status.HTTP_200_OK
            
            )
        except Exception as e:
            print(str(e))
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


class AccountsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        
        try:
            accounts = Accounts.objects.all()
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
    print(request.data)
    try:
        serializer = ContactsAsssignSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'contact assigned'}, status=status.HTTP_200_OK
            )
        return Response({'message':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(str(e))
        return Response({"error":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def account_overview(request):
    account_id = request.query_params.get("account_id")
    if not account_id:
        return Response({"detail": "Account ID is required."}, status=400)
    account = get_object_or_404(Accounts, id=account_id)
    serializer = AccountsViewSerializer(account)
    return Response(serializer.data)


class AccountCustomisedView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        print("Request data:", request.data)
        account_id = request.query_params.get("account_id")
        if not account_id:
            return Response({"detail": "Account ID is required."}, status=400)

        account = Accounts.objects.filter(id=account_id).first()
        if not account:
            return Response({"detail": "Account not found."}, status=404)

        print("Account before update:", account)
        key = request.data.get("key")
        value = request.data.get("value")
        is_editing = request.data.get("is_Editing")
        new_key = request.data.get("name")
        print(key,value,is_editing)

        if "key" in request.data:
            print(key)
            if not is_editing:
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

        print("Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=400)

    def delete(self,request):
        print(request.data)
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



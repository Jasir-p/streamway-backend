
from .models import Contact, Accounts
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ContactSerializer, ContactViewSerializer, AccountsSerilalizer, AccountsViewSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from tenant.pagination import StandardResultsSetPagination


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
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Contact created"}, status=status.HTTP_201_CREATED
            )
        
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
        


from .models import Contact
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ContactSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


# Create your views here.\

class ContactView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        contacts = Contact.objects.all()
        serializer = ContactSerializer(contacts, many=True)
        return Response(
            {"contacts": serializer.data}, status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Contact created"}, status=status.HTTP_201_CREATED
            )
        

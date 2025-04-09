from rest_framework import serializers
from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'  

    def create(self, validated_data):
        return Contact.objects.create(**validated_data)  
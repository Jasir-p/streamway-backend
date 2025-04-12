from rest_framework import serializers
from .models import Contact
from leads.models import Leads
from leads.serializers import LeadsGetSerializer


class ContactSerializer(serializers.ModelSerializer):
    
    lead = serializers.ListField(
            child=serializers.CharField(max_length=8),
            write_only=True,
            required=False
        )
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Contact
        fields = '__all__'

    def validate_lead(self, value):
        if isinstance(value, str):
            return [value]
        return value

    def validate_email(self, value):
        if value and '@' not in value:
            raise serializers.ValidationError('Invalid email')
        return value

    def validate_phone_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must be a digit")
        return value

    def create(self, validated_data):
        leads = [lead for lead in validated_data.pop('lead', []) if lead]
        leads_data = Leads.objects.filter(lead_id__in=leads)
        leads_dict = {lead.lead_id: lead for lead in leads_data}
        if leads:
            for lead in leads:
                lead_data = leads_dict.get(lead)
                contact = Contact.objects.create(
                    name=lead_data.name,
                    email=lead_data.email,
                    phone_number=lead_data.phone_number,
                    lead=lead_data
                    )
                contact.save()
            return True
        return Contact.objects.create(**validated_data) 


class ContactViewSerializer(serializers.ModelSerializer):
    lead = LeadsGetSerializer(read_only=True)
    
    class Meta:
        model = Contact
        fields = '__all__'
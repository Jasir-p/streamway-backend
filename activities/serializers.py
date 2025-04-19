from .models import Task,Attachment
from rest_framework import serializers
from users.models import Employee,Team
from django.contrib.contenttypes.models import ContentType
from leads.serializers import LeadsGetSerializer
from Customer.serializers import AccountsViewSerializer,ContactViewSerializer
from leads.models import Leads
from Customer .models import Accounts,Contact


class TaskSerializer(serializers.ModelSerializer):
    # Remove content_type and related_object
    lead = serializers.PrimaryKeyRelatedField(
        
        queryset=Leads.objects.all(), required=False, allow_null=True
    
    )
    contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(), required=False, allow_null=True
    )
    account = serializers.PrimaryKeyRelatedField(
        queryset=Accounts.objects.all(), required=False, allow_null=True
    )
    
    assigned_to_employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )
    assigned_to_team = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(), required=False, allow_null=True
    )
    assigned_by = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Task
        fields = "__all__"

    def get_related_object(self, obj):

        if obj.lead:
            return LeadsGetSerializer(obj.lead).data
        elif obj.contact:
            return ContactViewSerializer(obj.contact).data
        elif obj.account:
            return AccountsViewSerializer(obj.account).data
        return None

    def validate(self, attrs):

        return super().validate(attrs)



class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'file', 'file_name', 'upload_date']
    
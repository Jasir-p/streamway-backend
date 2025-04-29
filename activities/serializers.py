from .models import Task
from rest_framework import serializers
from users.models import Employee,Team
from django.contrib.contenttypes.models import ContentType
from leads.serializers import LeadsGetSerializer
from Customer.serializers import AccountsViewSerializer,ContactViewSerializer
from leads.models import Leads
from Customer .models import Accounts,Contact
from users.serializer import UserListViewSerializer


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
    attachment = serializers.FileField(required=False, allow_null=True)

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






class TaskViewSerializer(serializers.ModelSerializer):
    assigned_to_employee = UserListViewSerializer(read_only=True)
    lead = LeadsGetSerializer(read_only=True)
    contact = ContactViewSerializer(read_only=True)
    account = AccountsViewSerializer(read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
    
    def get_attachment_url(self, obj):
        request = self.context.get('request')
        print(request)
        if obj.attachment and hasattr(obj.attachment, 'url'):
            return request.build_absolute_uri(obj.attachment.url)
        return None
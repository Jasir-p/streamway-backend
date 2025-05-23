from .models import Task,Email
from rest_framework import serializers
from users.models import Employee,Team
from django.contrib.contenttypes.models import ContentType
from leads.serializers import LeadsGetSerializer
from Customer.serializers import AccountsViewSerializer,ContactViewSerializer
from leads.models import Leads
from Customer .models import Accounts,Contact
from users.serializer import UserListViewSerializer
from .tasks import tenant_mail_to

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
    created_by = serializers.PrimaryKeyRelatedField(
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
    assigned_by = UserListViewSerializer(read_only=True)
    created_by = UserListViewSerializer(read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
    
    def get_attachment_url(self, obj):
        request = self.context.get('request')
        print(request)
        if obj.attachment and hasattr(obj.attachment, 'url'):
            return request.build_absolute_uri(obj.attachment.url)
        return None
    

class EmailSerializer(serializers.ModelSerializer):
    to_lead = serializers.ListField(child=serializers.CharField(max_length=8),write_only=True, required=False)
    to_contacts = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    to_accounts = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    sender = UserListViewSerializer(read_only=True)
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), source='sender', write_only=True,required=False
    )

    class Meta:
        model = Email
        fields = '__all__'  
        extra_kwargs = {
            'to_lead': {'read_only': True},
            'to_contacts': {'read_only': True},
            'to_account': {'read_only': True},
        }
    
    def validate_to_lead(self, value):
        if isinstance(value, str):
            print(value)
            return [value]
        return value
    def __init__(self, *args, **kwargs):
        self.schema = kwargs.pop('schema', None) 
        super().__init__(*args, **kwargs)
    def create(self, validated_data):
        schema=self.schema
        to_leads = validated_data.pop("to_lead", [])
        print(to_leads)
        to_contacts = validated_data.pop("to_contacts", [])
        print("contatcs",to_contacts)
        to_accounts = validated_data.pop("to_accounts", [])
        print(to_accounts)

        created_emails = []
        print(to_leads)
        for lead_id in to_leads:
            lead = Leads.objects.get(lead_id=lead_id)
            email = Email.objects.create(**validated_data, to_lead=lead)
            created_emails.append(email)


        for contact_id in to_contacts:
            contact = Contact.objects.get(id=contact_id)
            email = Email.objects.create(**validated_data, to_contacts=contact)
            created_emails.append(email)


        for account_id in to_accounts:
            account = Accounts.objects.get(id=account_id)
            email = Email.objects.create(**validated_data, to_account=account)
            created_emails.append(email)

        tenant_mail_to.delay([email.id for email in created_emails],schema)
        return created_emails[0]  

class EmailsViewSerializer(serializers.ModelSerializer):
    to_lead = LeadsGetSerializer(read_only=True)
    to_contacts = ContactViewSerializer(read_only=True)
    to_account = AccountsViewSerializer(read_only=True)
    recipient = serializers.SerializerMethodField()
    sender = UserListViewSerializer(read_only =True)

    class Meta:
        model = Email
        fields = [
            'id', 'sender', 'category', 'is_sent', 'to_lead', 'to_contacts',
            'to_account', 'subject', 'body', 'created_at', 'updated_at', 
            'sent_at', 'recipient'
        ]

    def get_recipient(self, obj):
        if obj.to_lead:
            return LeadsGetSerializer(obj.to_lead).data
        if obj.to_contacts:
            return ContactViewSerializer(obj.to_contacts).data
        if obj.to_account:
            return AccountsViewSerializer(obj.to_account).data
        return None

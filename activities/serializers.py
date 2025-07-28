from .models import Task,Email,Meeting
from rest_framework import serializers
from users.models import Employee,Team
from django.contrib.contenttypes.models import ContentType
from leads.serializers import LeadsGetSerializer
from Customer.serializers import AccountsViewSerializer,ContactViewSerializer
from leads.models import Leads
from Customer .models import Accounts,Contact
from users.serializer import UserListViewSerializer,TeamViewserilizer
from .tasks import tenant_mail_to
from datetime import datetime
import re
from datetime import date, time as time_obj


FORBIDDEN_TITLE_CHARS_REGEX = re.compile(r"[\/\-_]")
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
    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title is required")
        if FORBIDDEN_TITLE_CHARS_REGEX.search(value):
            raise serializers.ValidationError("Title cannot contain  '/', '-', or '_'.")
        return value
    
    def validate_description(self, value):
        word = value.strip()
        if not word:
            raise serializers.ValidationError("Description is required")
        if len(word) < 30:
            raise serializers.ValidationError("Description should be at least 30 characters long")
        return value
    
    def validate_duedate(self, value):
        if not value:
            raise serializers.ValidationError("Due date is required")
        if value < date.today():
            raise serializers.ValidationError("Due date cannot be in the past")

    def validate(self, attrs):
        
        return super().validate(attrs)
    
    def create(self, validated_data):
        is_team = validated_data.get('assigned_to_team')
        if is_team:
            validated_data['is_team']=True
            validated_data['assigned_to_employee']=is_team.team_lead

        
        return super().create(validated_data)







class TaskViewSerializer(serializers.ModelSerializer):
    assigned_to_employee = UserListViewSerializer(read_only=True)
    assigned_to_team = TeamViewserilizer(read_only=True)
    lead = LeadsGetSerializer(read_only=True)
    contact = ContactViewSerializer(read_only=True)
    account = AccountsViewSerializer(read_only=True)
    assigned_by = UserListViewSerializer(read_only=True)
    created_by = UserListViewSerializer(read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
    
    

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
            return [value]
        return value
    def __init__(self, *args, **kwargs):
        self.schema = kwargs.pop('schema', None) 
        super().__init__(*args, **kwargs)
    def create(self, validated_data):
        schema=self.schema
        to_leads = validated_data.pop("to_lead", [])
        to_contacts = validated_data.pop("to_contacts", [])
        to_accounts = validated_data.pop("to_accounts", [])

        created_emails = []
        for lead_id in to_leads:
            lead = Leads.objects.get(lead_id=lead_id)
            email = Email.objects.create(**validated_data, to_lead=lead,recipient_name=lead.name,recipient_email=lead.email)
            created_emails.append(email)


        for contact_id in to_contacts:
            contact = Contact.objects.get(id=contact_id)
            email = Email.objects.create(**validated_data, to_contacts=contact,recipient_name=contact.name,recipient_email=contact.email)
            created_emails.append(email)


        for account_id in to_accounts:
            account = Accounts.objects.get(id=account_id)
            email = Email.objects.create(**validated_data, to_account=account,recipient_name=account.name,recipient_email=account.email)
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
            'sent_at', 'recipient','recipient_name','recipient_email'
        ]

    def get_recipient(self, obj):
        if obj.to_lead:
            return LeadsGetSerializer(obj.to_lead).data
        if obj.to_contacts:
            return ContactViewSerializer(obj.to_contacts).data
        if obj.to_account:
            return AccountsViewSerializer(obj.to_account).data
        return None

class MeetingSerializer(serializers.ModelSerializer):
    host = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )
    date = serializers.DateField(write_only=True)
    time = serializers.TimeField(write_only=True)
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )
    contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'description', 'date', 'time', 'start_time',
            'duration', 'host', 'status', 'contact','created_by'
        ]
        read_only_fields = ['start_time']
    

    def validate_date(self, value):
        
        if not value:
            raise serializers.ValidationError('Date is required')
        if value < date.today():
            raise serializers.ValidationError("Date cannot be in the past.")
        return value
    def validate_time(self, value):
        
        if not value:
            raise serializers.ValidationError('Time is required')
        if not (time_obj(9, 0) <= value <= time_obj(20, 0)):
            raise serializers.ValidationError("Time must be between 09:00 and 18:00.")
        return value
    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title is required")
        if FORBIDDEN_TITLE_CHARS_REGEX.search(value):
            raise serializers.ValidationError("Title cannot contain  '/', '-', or '_'.")
        return value
    

    def create(self, validated_data):
        date = validated_data.pop('date')
        time = validated_data.pop('time')
        validated_data['start_time'] = datetime.combine(date, time)



        return super().create(validated_data)

    def update(self, instance, validated_data):
        date = validated_data.pop('date', None)
        time = validated_data.pop('time', None)

        if date and time:
            validated_data['start_time'] = datetime.combine(date, time)

        return super().update(instance, validated_data)

class MeetingViewSerializer(serializers.ModelSerializer):
    host = UserListViewSerializer(read_only =True)
    created_by = UserListViewSerializer(read_only =True)
    contact = ContactViewSerializer(read_only =True)
    

    class Meta:
        model = Meeting
        fields = "__all__"
    
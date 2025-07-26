from rest_framework import serializers
from .models import Contact,Accounts,Notes
from leads.models import Leads,Deal

from users.models import Employee
from users.serializer import UserListViewSerializer
from django.utils import timezone
import re
from tenant_panel.constants import (
    EMAIL_REGEX,
    CONTACT_REGEX,
    NAME_REGEX,NOTES_HAS_ALPHANUMERIC_REGEX,
    NOTES_START_REGEX,
    CUSTOM_FIELD_NAME_REGEX,
    CUSTOM_FIELD_VALUE_REGEX,
    REPEATED_CHARACTER_PATTERN)


class ContactSerializer(serializers.ModelSerializer):
    account_id = serializers.PrimaryKeyRelatedField(
        queryset=Accounts.objects.all(), required=False, allow_null=True
    )
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Contact
        fields = '__all__'



    def validate_email(self, value):
        value=value.strip()
        if not value:
            raise serializers.ValidationError("Email is required")
        if not re.match(EMAIL_REGEX, value):
            raise serializers.ValidationError("Invalid Email")
        contact_id = self.instance.id if self.instance else None
        if Contact.objects.filter(email=value).exclude(id=contact_id).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate_phone_number(self, value):
        if not re.match(CONTACT_REGEX, value):
            raise serializers.ValidationError("Invalid Phone Number")
        contact_id = self.instance.id if self.instance else None
        if Contact.objects.filter(phone_number=value).exclude(id=contact_id).exists():
            raise serializers.ValidationError("Phone number already exists")
        
        return value
    def validate_name(self, value):
        value=value.strip()
        if not value:
            raise serializers.ValidationError("Name is required")
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        if not re.match(NAME_REGEX, value):
            raise serializers.ValidationError("Invalid Name")
        return value
    def validate_department(self,value):
        value=value.strip()
        contact_id = self.instance.id if self.instance else None
        if contact_id:
            is_primary = Contact.objects.get(id=contact_id).is_primary_contact

        if not value and not is_primary:
            raise serializers.ValidationError("Department is required")
        if not re.match(NAME_REGEX, value) and not is_primary:
            raise serializers.ValidationError("Invalid Department")
        
        return value
    def validate_account_id(self, value):
        if not value:
            raise serializers.ValidationError("Account ID is required")
        return value

    def create(self, validated_data):
        return Contact.objects.create(**validated_data) 




class AccountsSerilalizer(serializers.ModelSerializer):
    lead = serializers.ListField(
            child=serializers.CharField(max_length=8),
            write_only=True,
            required=False
        )
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Accounts
        fields = '__all__'

    def validate_lead(self, value):
        if isinstance(value, str):
            return [value]
        return value
    
    def validate_email(self, value):
        value=value.strip()
        if not value:
            raise serializers.ValidationError("Email is required")
        if not re.match(EMAIL_REGEX, value):
            raise serializers.ValidationError("Invalid Email")
        return value

    def validate_phone_number(self, value):
        if not re.match(CONTACT_REGEX, value):
            raise serializers.ValidationError("Invalid Phone Number")
        return value
    def validate_name(self, value):
        value=value.strip()
        if not value:
            raise serializers.ValidationError("Name is required")
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        if not re.match(NAME_REGEX, value):
            raise serializers.ValidationError("Invalid Name")
        return value
    def create(self, validated_data):

        leads = [lead for lead in validated_data.pop('lead', []) if lead]
        is_deal = self.initial_data.get("create_deal", False)
        deal_amount= self.initial_data.get("deal_amount", 0)
        assigned_by = validated_data.pop('assigned_by', None)
        leads_data = Leads.objects.filter(lead_id__in=leads)
        leads_dict = {lead.lead_id: lead for lead in leads_data}
        if leads:
            for lead in leads:
                lead_data = leads_dict.get(lead)
                if not Accounts.objects.filter(email=lead_data.email).exists():
                    account = Accounts.objects.create(
                        name=lead_data.name,
                        email=lead_data.email,
                        phone_number=lead_data.phone_number,
                        address =lead_data.location,
                        lead=lead_data,
                        assigned_to=lead_data.employee,
                        assigned_by=assigned_by

                    )
                    Contact.objects.create(
                        name=lead_data.name,
                        email=lead_data.email,
                        phone_number=lead_data.phone_number,
                        account_id=account,
                        is_primary_contact =True
                    )

                    if is_deal:

                        date_str= timezone.now().strftime("%Y-%m-%d")
                        Deal.objects.create(
                            account_id=account,
                            title = f"Deal for {account.name} at {date_str}",
                            owner = account.assigned_to,
                            created_by = account.assigned_by,
                            amount=deal_amount,
                            expected_close_date= timezone.now().date() + timezone.timedelta(days=30),)
                    
                
            return True
        return Accounts.objects.create(**validated_data)
    


class AccountsViewSerializer(serializers.ModelSerializer):
    lead = serializers.SerializerMethodField()
    assigned_to = UserListViewSerializer(read_only=True)
    assigned_by = UserListViewSerializer(read_only=True)

    class Meta:
        model = Accounts
        fields = '__all__'

    def get_lead(self, obj):
        from leads.serializers import LeadsGetSerializer 
        if obj.lead:
            return LeadsGetSerializer(obj.lead).data
        return None


class ContactViewSerializer(serializers.ModelSerializer):
    account_id = AccountsViewSerializer(read_only=True)
    assigned_to =UserListViewSerializer(read_only=True)
    assigned_by =UserListViewSerializer(read_only=True)
    
    class Meta:
        model = Contact
        fields = '__all__'



class ContactsAsssignSerializer(serializers.Serializer):
    contact_id = serializers.ListField(child=serializers.IntegerField(),required=True)
    assigned_to = serializers.IntegerField(required=True)
    assigned_by = serializers.IntegerField(allow_null=True)

    

    def validate(self, data):

        assigned_to = data.get("assigned_to")
        assigned_by = data.get("assigned_by")

        if not Employee.objects.filter(id =assigned_to).exists():
            raise serializers.ValidationError("Employee not found")
        if assigned_by is not None and not Employee.objects.filter(id=assigned_by).exists():
            raise serializers.ValidationError({"granted_by": "Granter not found"})
        
        if not Contact.objects.filter(id__in=data.get("contact_id")).exists():
            raise serializers.ValidationError("Contact not found")
        
        return data

    def save(self, **kwargs):
        assigned_to = Employee.objects.get(id=self.validated_data.get("assigned_to"))
        assigned_by_id = self.validated_data.get("assigned_by")
        assigned_by = Employee.objects.get(id=assigned_by_id) if assigned_by_id else None
        contacts = Contact.objects.filter(id__in=self.validated_data.get("contact_id"))
        contacts.update(assigned_to=assigned_to, assigned_by=assigned_by)


class AccountCustomizedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accounts
        fields = '__all__'

    def validate(self, data):
        if 'custome_fields' in data:
            key= data['key']
            value = data['value']
            instance_custom_fields = self.instance.custome_fields if self.instance and self.instance.custome_fields else {}
            key = key.strip()
            value = value.strip()

            if key in instance_custom_fields:
                raise serializers.ValidationError(f"Field '{key}' already exists in custom fields.")
            if not re.match(CUSTOM_FIELD_NAME_REGEX,key):
                raise serializers.ValidationError(
                    f"Field name must start with a letter and contain only letters, numbers, spaces, underscores, or dashes."
                    )
            if value.isdigit():
             raise serializers.ValidationError("Field name cannot be only numbers.")
        
            if re.match(REPEATED_CHARACTER_PATTERN, key):
                raise serializers.ValidationError("Field name cannot be the same character repeated.")
            if key.endswith("-") or  key.endswith('_'):
                raise serializers.ValidationError("Field name cannot end with a hyphen or underscore.")
            if not value or not re.match(CUSTOM_FIELD_VALUE_REGEX,value):
                raise serializers.ValidationError(f" Field value contains invalid characters.")
        return data
    

class AccountNotesSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )
    account  = serializers.PrimaryKeyRelatedField(
        queryset=Accounts.objects.all(), required=False, allow_null=True
    )
    class Meta:
        model = Notes
        fields = '__all__'

    def validate_notes(self,value):
        words = value.strip().split()
        if not words:
            raise serializers.ValidationError("Notes cannot be empty")
        if len(words)<5:
            raise serializers.ValidationError("Notes should be at least 5 words")
        if not re.match(NOTES_START_REGEX, value):
            raise serializers.ValidationError("Notes must start with a letter or number.")
        if not re.match(NOTES_HAS_ALPHANUMERIC_REGEX,value):
            raise serializers.ValidationError("Notes cannot contain only special characters.")
        return value
    
    def validate_account(self, value):
        if not value:
            raise serializers.ValidationError("Account is required")
        return value
 
    
class AccountNoteViewSerializer(serializers.ModelSerializer):
    created_by = UserListViewSerializer(read_only=True)
    account = AccountsViewSerializer(read_only=True)
    class Meta:
        model = Notes
        fields = '__all__'


class AccountAssignSerializer(serializers.Serializer):
    assigned_to = serializers.IntegerField(required=True)
    assigned_by = serializers.IntegerField(allow_null=True)
    account_id = serializers.ListField(child=serializers.IntegerField(),required=True)


    def validate(self, data):
        assigned_by = data.get("assigned_by")
        assigned_to = data.get("assigned_to")

        if not Employee.objects.filter(id =assigned_to).exists():
            raise serializers.ValidationError("Employee not found")
        if assigned_by is not None and not Employee.objects.filter(id=assigned_by).exists():
            raise serializers.ValidationError({"granted_by": "Granter not found"})
        
        if not Accounts.objects.filter(id__in=data.get("account_id")).exists():
            raise serializers.ValidationError("Account not found")
        
        return data
    
    def save(self, **kwargs):
        assigned_to = Employee.objects.get(id=self.validated_data.get("assigned_to"))
        assigned_by_id = self.validated_data.get("assigned_by")
        assigned_by = Employee.objects.get(id=assigned_by_id) if assigned_by_id else None
        accounts = Accounts.objects.filter(id__in=self.validated_data.get("account_id"))
        accounts.update(assigned_to=assigned_to, assigned_by=assigned_by)
        for account in accounts:
            account.contacts.update(assigned_to=assigned_to, assigned_by=assigned_by)
        


from rest_framework import serializers
from .models import LeadFormField, Leads,WebForm,LeadNotes,Deal,DealNotes
from users.models import Employee
from users.serializer import EmployeeSerializer,UserListViewSerializer
from .tasks import create_lead_from_webform
from tenant.utlis.get_tenant import get_schema_name
from Customer.models import Accounts
from Customer.serializers import AccountsViewSerializer




class LeadFormSerializers(serializers.ModelSerializer):
    class Meta:
        model = LeadFormField
        fields = '__all__'

        extra_kwargs = {
                'field_name': {'required': True},
                'field_type': {'required': True},
            
            }
        
    def validate_field_name(self, value):
        field_id = self.instance.id if self.instance else None
        if LeadFormField.objects.filter(field_name=value).exclude(
                id=field_id).exists():
            raise serializers.ValidationError('Field name already exists')

        return value
    
    def create(self, validated_data):
        return super().create(validated_data)


class LeadSerializers(serializers.ModelSerializer):
    form_data = serializers.ListField(
        child=serializers.CharField(max_length=8),
        write_only=True,
        required=False
    )
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )
    granted_by = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )

    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Leads
        fields = '__all__'

        
        # extra_kwargs = {
        #     'name': {'required': True},
        #     'email': {'required': True},
        #     'phone_number': {'required': True},
            
        # }

    def validate_form_data(self, value):
        if isinstance(value, str):
            return [value]
        return value

    def validate_email(self, value):
        if not value.endswith(".com"):
            raise serializers.ValidationError("Email must be a .com email")
        return value
    
    def validate_phone_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must be a digit")
        return value
    
    def to_internal_value(self, data):

        print(data)
        model_fields = {field.name for field in Leads._meta.get_fields()}
        self.custom_fields = {k: v for k, v in data.items()
                              if k not in model_fields}
        print(self.custom_fields)
        return super().to_internal_value(data)
    
    def __init__(self, *args, **kwargs):
        self.schema = kwargs.pop('schema', None)  # Pop schema from kwargs
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        schema = self.schema
        form_data_list = [form for form in validated_data.pop('form_data', [])]
        
        if form_data_list:
            web_forms = WebForm.objects.filter(web_id__in=form_data_list)
            web_form_dict = {form.web_id: form for form in web_forms}
            employee = validated_data.pop("employee", None)
            granted_by = validated_data.pop("granted_by", None)

            validated_data_serializable = validated_data.copy()
            if employee:
                validated_data_serializable["employee"] = employee.id
            if granted_by:
                validated_data_serializable["granted_by"] = granted_by.id
            
            create_lead_from_webform.delay(
                form_data_list, validated_data_serializable, schema
            )
            return {"message": "Leads creation task started."}
            
        else:
            lead = Leads.objects.create(**validated_data)
            if self.custom_fields:
                lead.custome_fields = self.custom_fields
                lead.save()
            return lead

   


class LeadsGetSerializer(serializers.ModelSerializer):
    employee = UserListViewSerializer(read_only=True)
    granted_by = UserListViewSerializer(read_only=True)

    class Meta:
        model = Leads
        fields = '__all__'



class WebformSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = WebForm
        fields = '__all__'
        extra_kwargs = {
            'name': {'required': True},
            'email': {'required': True},
            'phone_number': {'required': True},
            
        }

    def validate_email(self, value):
        if not value.endswith(".com"):
            raise serializers.ValidationError("Email must be a .com email")
        return value
    
    def validate_phone_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must be a digit")
        return value
    
    def to_internal_value(self, data):

        print(data)
        model_fields = {field.name for field in WebForm._meta.get_fields()}
        self.custom_fields = {k: v for k, v in data.items()
                              if k not in model_fields}
        print(self.custom_fields)
        return super().to_internal_value(data)

    def create(self, validated_data):
        lead = WebForm.objects.create(**validated_data)
        if self.custom_fields:
            print(self.custom_fields)
            lead.custome_fields = self.custom_fields
            lead.save()
        return lead



class WebformListViewSerializer(serializers.ModelSerializer):
    employee = serializers.SerializerMethodField()
    granted_by = serializers.SerializerMethodField()
    lead_created = serializers.SerializerMethodField()

    class Meta:
        model = WebForm
        fields = [
            "web_id",
            "name",
            "email",
            "phone_number",
            "location",
            "created_at",
            "updated_at",
            "status",
            "custome_fields",
            "employee",
            "granted_by",
            "lead_created",
            'source',
        ]
    def get_employee(self, obj):
        if hasattr(obj, "employee") and obj.employee:
            employee = Employee.objects.filter(id=obj.employee).first()
            return {"id": employee.id, "name": employee.name} if employee else None
        return None

    def get_granted_by(self, obj):
        if hasattr(obj, "granted_by") and obj.granted_by:
            granted_by = Employee.objects.filter(id=obj.granted_by).first()
            return {"id": granted_by.id, "name": granted_by.name} if granted_by else None
        return None
    
    def get_lead_created(self, obj):
        return hasattr(obj, "lead_created") and obj.lead_created
    




class LeadAssignSerializer(serializers.Serializer):
    lead_id = serializers.ListField(
        child=serializers.CharField(), 
        required=True
    )
    employee = serializers.IntegerField(required=True)
    granted_by = serializers.IntegerField(allow_null=True)

    
    def validate(self, data):

        employee = data.get("employee")
        granted_by = data.get("granted_by")

        if not Employee.objects.filter(id =employee).exists():
            raise serializers.ValidationError("Employee not found")
        if granted_by is not None and not Employee.objects.filter(id=granted_by).exists():
            raise serializers.ValidationError({"granted_by": "Granter not found"})
        
        if not Leads.objects.filter(lead_id__in=data.get("lead_id")).exists():
            raise serializers.ValidationError("Lead not found")
        
        return data
    
    def save(self):
        employee = Employee.objects.get(id=self.validated_data["employee"])
        granted_by_id = self.validated_data.get("granted_by")
        granted_by = Employee.objects.get(id=granted_by_id)if granted_by_id is not None else None
        leads = Leads.objects.filter(lead_id__in=self.validated_data["lead_id"])
        
        leads.update(employee=employee, granted_by=granted_by)

        return {"message": "Sucessfully updated"}

class LeadNoteSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )
    lead  = serializers.PrimaryKeyRelatedField(
        queryset=Leads.objects.all(), required=False, allow_null=True
    )
    class Meta:
        model = LeadNotes
        fields = "__all__"

class LeadNoteViewSerializer(serializers.ModelSerializer):
    created_by = UserListViewSerializer(read_only=True)
    lead = LeadsGetSerializer(read_only=True)
    class Meta:
        model = LeadNotes
        fields = "__all__"
class DealsSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )
    owner = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )
    account_id = serializers.PrimaryKeyRelatedField(
        queryset=Accounts.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = Deal
        fields = "__all__"


    def validate(self, attrs):
        return super().validate(attrs)
        

class DealsViewserializer(serializers.ModelSerializer):
    created_by = UserListViewSerializer(read_only=True)
    owner = UserListViewSerializer(read_only=True)
    account_id = AccountsViewSerializer(read_only=True)

    class Meta:
        model = Deal
        fields = "__all__"

    
class DealNotesSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(), required=False, allow_null=True
    )
    deal  = serializers.PrimaryKeyRelatedField(
        queryset=Deal.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = DealNotes
        fields = "__all__"

class DealNotesViewSerializer(serializers.ModelSerializer):
    created_by = UserListViewSerializer(read_only=True)
    deal = DealsViewserializer(read_only=True)

    class Meta:
        model = DealNotes
        fields = "__all__"
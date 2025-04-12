from celery import shared_task
from leads.models import Leads, WebForm
from users.models import Employee
from django_tenants.utils import schema_context

@shared_task
def create_lead_from_webform(form_data_list, validated_data_dict, schema):
    
    with schema_context(schema):  # Switch to the tenant schema
        print(f"Running task in schema: {schema}")
        print(form_data_list)
        
        # Retrieve the WebForms based on the provided form_data_list
        web_forms = WebForm.objects.filter(web_id__in=form_data_list)
        web_form_dict = {form.web_id: form for form in web_forms}

        employee_id = validated_data_dict.get("employee")
        granted_by_id = validated_data_dict.get("granted_by")
        employee = Employee.objects.get(id=employee_id) if employee_id else None
        granted_by = Employee.objects.get(id=granted_by_id) if granted_by_id else None
        
        for form_data in form_data_list:
            web_form = web_form_dict.get(form_data)
            if web_form:
                lead = Leads.objects.create(
                    form_data=web_form,
                    name=web_form.name,
                    email=web_form.email,
                    phone_number=web_form.phone_number,
                    location=web_form.location,
                    employee=employee,
                    granted_by=granted_by,
                    custome_fields=web_form.custome_fields
                )

        return True

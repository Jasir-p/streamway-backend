from celery import shared_task
from leads.models import Leads, WebForm
from users.models import Employee
from tenant.models import Tenant
from django_tenants.utils import schema_context


@shared_task
def create_lead_from_webform(form_data_list, validated_data, ):
    # print(tenants)
    # try:
    #     tenant = Tenant.objects.get(schema_name=tenants.schema_name)
    # except Tenant.DoesNotExist:
    #     print(f"Tenant {tenant.name} does not exist!")
    #     return

    # with schema_context(tenant.schema_name):  # Switch to the tenant schema
    #     print(f"Running task in schema: {tenant.schema_name}")
    print(form_data_list)
    web_forms = WebForm.objects.filter(web_id__in=form_data_list)
    web_form_dict = {form.web_id: form for form in web_forms}
    employee = Employee.objects.get(id=validated_data["employee"]) if validated_data.get("employee") else None
    granted_by = Employee.objects.get(id=validated_data["granted_by"]) if validated_data.get("granted_by") else None
    lead_access = []
    for form_data in form_data_list:
                
        web_form = web_form_dict.get(form_data)
        print("custome",web_form.custome_fields)
                    
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
        lead_access.append(lead)
                       
    return lead_access
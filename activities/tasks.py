from celery import shared_task
from.models import Email,Task
from .utlis.send_tenant_email import send_tenant_email
from django_tenants.utils import schema_context
from tenant.models import Tenant
from datetime import date

@shared_task
def tenant_mail_to(email_ids,schema):
    try:
        #send mail from tenant
        print("celaryyyy")
        with schema_context(schema):
            tenant = Tenant.objects.get(schema_name=schema)
            emails = Email.objects.filter(id__in=email_ids)

            for email in emails:
              
                data = (
                    email.to_lead
                    or email.to_account
                    or email.to_contacts
                    or None
                )

                recipient =(
                    email.to_lead.email if email.to_lead else
                    email.to_contacts.email if email.to_contacts else
                    email.to_account.email if email.to_account else
                    None
                )
                if recipient:
                    send_tenant_email(tenant=tenant,
                                      data=data,
                                    subject=email.subject,
                                    to_email=recipient,
                                    body=email.body,
                                    template = email.category,
                                    instance = email
                       
                                    )
                    email.is_sent = True
                    email.save()

            return True
    
    except Exception as e:
        print(str(e))
        return str(e)

@shared_task
def task_due_info():
    tenants=Tenant.objects.filter(is_active=True)

    for tenant in tenants:
        check_due_date.delay(tenant.schema_name)
    
    return f"task_due_info executed for {len(tenants)} tenants"


        
@shared_task
def check_due_date(schema):
    with schema_context(schema):
        # Get all due dates for the tenant
        tasks = Task.objects.all().exclude(status="COMPLETED")

        for task in tasks:
            remainig_day = (task.duedate - date.today()).days

            if remainig_day ==1:
                print("remaining one day")

            if remainig_day ==0:
                print("remaining zero day")

            if remainig_day <0:
                print("remaining negative day")

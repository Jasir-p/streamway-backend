from celery import shared_task
from.models import Email,Task
from .utlis.send_tenant_email import send_tenant_email
from django_tenants.utils import schema_context
from tenant.models import Tenant
from datetime import date
from django.utils import timezone
from communications.utlis.notification_handler import notification_set
import logging
from communications.models import Notifications
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from users.models import Employee

logger = logging.getLogger(__name__)

@shared_task
def tenant_mail_to(email_ids,schema):
    try:

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
                    email.sent_at = timezone.now()
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


        
from celery import shared_task
from datetime import date
from django_tenants.utils import schema_context
from tenants.models import Tenant  # adjust import if needed
from activities.models import Task  # adjust as per your project
from users.models import Employee  # adjust if needed
from core.utils import send_tenant_email  # your utility for sending emails
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_due_date(schema):
    with schema_context(schema):
        tenant = Tenant.objects.get(schema_name=schema)

        tasks = Task.objects.exclude(status="COMPLETED")
        today = date.today()
        logger.info(f"➡️ Running check_due_date for {len(tasks)} tasks (today={today})")

        for task in tasks:
            remaining_day = (task.duedate - today).days
            employee = task.assigned_to_employee

            if remaining_day == 1:
                message = f'"{task.title}" Due date is Tomorrow'
                logger.info("Prepared 'due tomorrow' email")

            elif remaining_day == 0:
                message = f'"{task.title}" Due date is Today'
                logger.info("Prepared 'due today' email")

            elif remaining_day < 0:
                message = f'"{task.title}" Due date is over'
                logger.info("Prepared 'overdue' email")

            else:
                continue  


            if employee and employee.email:
                send_tenant_email(
                    tenant=tenant,
                    data=employee,
                    subject="Task Reminder",
                    to_email=employee.email,
                    body=message
                )
                logger.info(f"Email sent to {employee.email}")

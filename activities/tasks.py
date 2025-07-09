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


        
@shared_task
def check_due_date(schema):
    with schema_context(schema):

        tasks = Task.objects.all().exclude(status="COMPLETED")
        today = date.today()
        logger.info(f"➡️  Running check_due_date for {len(tasks)} tasks (today={today})")
        for task in tasks:
            logger.info(f"➡️  Running check_due_date for {len(tasks)} tasks (due={task.duedate})")
            remainig_day = (task.duedate - date.today()).days
            logger.info(f"➡️  Running check_due_date for {len(tasks)} tasks (today={remainig_day})")

            if remainig_day ==1:
                send_due_message.delay(message=f'''"{task.title}"Due date is Tomorrow''',user_id=task.assigned_to_employee.id,schema=schema)
                logger.info("sent 'due tomorrow' notification")

            elif remainig_day ==0:
                send_due_message.delay(message=f'''"{task.title}"Due date is Today''',user_id=task.assigned_to_employee.id,schema=schema)
                logger.info("remaining zero day")

            elif remainig_day <0:
                send_due_message.delay(message=f'''"{task.title}"Due date is over''',user_id=task.assigned_to_employee.id,schema=schema)
                logger.info("remaining negative day")


@shared_task
def send_due_message(message,user_id,schema_name):
    from django_tenants.utils import schema_context

    with schema_context(schema_name):
        user=Employee.objects.get(id=user_id)
        saved = Notifications.objects.create(
            type='Task',
            message=message,
            user=user
        )

        channel_layer = get_channel_layer()
        if channel_layer is not None:
                # Prepare message data
                data = {
                    "type": "user.notification",
                    "data": {
                        "id": saved.id,
                        "type": "Task",
                        "message": message,
                    }
                }

                # Only use async call after DB operations
                user_ids = user.user.id
                async_to_sync(channel_layer.group_send)(f"user-{user_ids}", data)

        
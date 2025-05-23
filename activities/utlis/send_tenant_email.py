from django.core.mail import EmailMessage
from email.utils import formataddr
from django.template.loader import render_to_string

def send_tenant_email(tenant, to_email, subject,instance, body=None, template=None, data=None):
    if template:
        context = {
            'tenant': tenant,
            'data': data or {},
            'instance': instance
        }
        body = render_to_string(f"emails/{template}.html", context)
    else:
        context = {
            'tenant': tenant,
            "data": data or {},
            'subject':subject,
            'body': body,
            'instance': instance
            }
        body = render_to_string(f"emails/defualt.html", context)

    from_email = formataddr((f"{tenant.name} Team", f"noreply@streamway.com"))
    
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=[to_email]
    )
    
    email.content_subtype = "html"  
    email.send(fail_silently=False)

import stripe
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from datetime import datetime,timedelta
from tenant.models import TenantBilling, Invoice

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    """
    print("firsttt")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:

        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:

        return HttpResponse(status=400)
    
    print(event.type) # Handle the event
    if event.type == 'invoice.paid':
        handle_invoice_paid(event.data.object)
    elif event.type == 'invoice.payment_failed':
        handle_invoice_payment_failed(event.data.object)
    elif event.type == 'customer.subscription.deleted':
        handle_subscription_deleted(event.data.object)
    elif event.type == 'payment_intent.succeeded':
        handle_payment_succeeded(event.data.object)
    # Add more event types as needed
    
    return HttpResponse(status=200)

def handle_invoice_paid(invoice_obj):
    """
    Handle when an invoice is paid
    """
    print("webinvoice2")
    try:
        # Find the invoice in our database
        invoice = Invoice.objects.get(stripe_invoice_id=invoice_obj.id)
        invoice.status = 'paid'
        invoice.paid_at = datetime.now()
        invoice.invoice_pdf_url = invoice_obj.invoice_pdf
        invoice.save()
        
        # Update the tenant billing next billing date
        billing = invoice.tenant_billing
        billing.last_billed_date = datetime.now()
        billing.save()
    except Invoice.DoesNotExist:
        # Log error or handle missing invoice
        pass

def handle_invoice_payment_failed(invoice_obj):
    """
    Handle when an invoice payment fails
    """
    try:
        invoice = Invoice.objects.get(stripe_invoice_id=invoice_obj.id)
        invoice.status = 'failed'
        invoice.save()
        
        # You might want to send an email to the tenant admin here
    except Invoice.DoesNotExist:
        # Log error or handle missing invoice
        pass

def handle_subscription_deleted(subscription_obj):
    """
    Handle when a subscription is deleted (if you decide to use subscriptions)
    """
    # If you implement subscription-based billing later
    pass

def handle_payment_succeeded(payment_intent):
    """
    Handle when a payment intent succeeds
    """
    print("webinvoice1")
    try:
        invoice = Invoice.objects.get(stripe_payment_intent_id=payment_intent.id)
        invoice.status = 'paid'
        invoice.paid_at = datetime.now()
        invoice.save()

        billing = invoice.tenant_billing
        billing.last_billed_date = datetime.now()
        billing.last_billing_status= True
        billing.save()
    except Invoice.DoesNotExist:
        pass
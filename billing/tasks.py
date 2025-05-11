import stripe
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from django_tenants.utils import tenant_context, get_tenant_model
from tenant.models import TenantBilling, Invoice

stripe.api_key = settings.STRIPE_SECRET_KEY

@shared_task
def check_all_tenants_billing():
    """
    Task to check all tenants for billing
    This task will run periodically (e.g., daily) to check all tenants
    """
    # Get all tenants
    Tenant = get_tenant_model()
    tenants = Tenant.objects.all()
    
    # Process each tenant
    for tenant in tenants:
        check_tenant_billing.delay(tenant.id)
    
    return f"Scheduled billing checks for {len(tenants)} tenants"

@shared_task
def check_tenant_billing(tenant_id):
    """
    Check if a specific tenant needs to be billed
    """
    Tenant = get_tenant_model()
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
        
        # Use tenant context to ensure we're using the right schema
        with tenant_context(tenant):
            try:
                # Get tenant billing info
                billing = TenantBilling.objects.get(tenant=tenant)
                

                if not billing.is_active:
                    return f"Billing is inactive for tenant {tenant.name}"
                

                now = timezone.now()
                print("bill",billing.next_billing_date)
                print("checktime",now)
                
                if billing.next_billing_date and billing.next_billing_date <= now:
                    print("bill",billing.next_billing_date)
                    print("checktime",now)

                    generate_invoice.delay(billing.id)
                    return f"Billing initiated for tenant {tenant.name}"
                else:
                    next_date = billing.next_billing_date or "Not set"
                    return f"Not yet time to bill tenant {tenant.name}. Next billing date: {next_date}"
                
            except TenantBilling.DoesNotExist:
                return f"No billing setup found for tenant {tenant.name}"
                
    except Tenant.DoesNotExist:
        return f"Tenant with ID {tenant_id} not found"

@shared_task
def generate_invoice(tenant_billing_id):
    """
    Generate invoice for a tenant
    """
    try:
        billing = TenantBilling.objects.get(id=tenant_billing_id)

        with tenant_context(billing.tenant):

            amount, user_count = billing.calculate_bill_amount()
            print("amount",amount)
            
            if amount <= 0:
                return f"No users to bill for tenant {billing.tenant.name}"

            try:

                payment_intent = stripe.PaymentIntent.create(
                    amount=int(amount * 100), 
                    currency='usd',
                    customer=billing.stripe_customer_id,
                    description=f"Monthly billing for {billing.tenant.name} - {user_count} users",
                    metadata={
                        'tenant_id': billing.tenant.id,
                        'billing_id': billing.id,
                        'user_count': user_count
                    }
                )
                

                invoice = Invoice.objects.create(
                    tenant_billing=billing,
                    stripe_payment_intent_id=payment_intent.id,
                    amount=amount,
                    user_count=user_count,
                    status='pending'
                )
                

                stripe_invoice = stripe.Invoice.create(
                    customer=billing.stripe_customer_id,
                    collection_method='send_invoice',
                    days_until_due=14,  # Due in 14 days
                    description=f"Monthly billing for {billing.tenant.name} - {user_count} users",
                    metadata={
                        'tenant_id': billing.tenant.id,
                        'invoice_id': invoice.id
                    }
                )
                

                stripe.InvoiceItem.create(
                    customer=billing.stripe_customer_id,
                    amount=int(amount * 100),  # Convert to cents
                    currency='usd',
                    description=f"Monthly service fee for {user_count} users",
                    invoice=stripe_invoice.id
                )
                

                stripe.Invoice.finalize_invoice(stripe_invoice.id)

                stripe.Invoice.send_invoice(stripe_invoice.id)
                

                invoice.stripe_invoice_id = stripe_invoice.id
                invoice.save()
                billing.next_billing_date = timezone.now() + timedelta(days=30)
                billing.save()
                
                return f"Invoice generated for tenant {billing.tenant.name}, amount: ${amount}, users: {user_count}"
                
            except stripe.error.StripeError as e:

                return f"Stripe error for tenant {billing.tenant.name}: {str(e)}"
                
    except TenantBilling.DoesNotExist:
        return f"Tenant billing with ID {tenant_billing_id} not found"
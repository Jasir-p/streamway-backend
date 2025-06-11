from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from datetime import datetime, timedelta
from django.utils.translation import gettext_lazy as _
import re
import random
import string
import stripe
from django.conf import settings
from django_tenants.utils import schema_context
from django_tenants.signals import post_schema_sync
from django.dispatch import receiver
from django.utils import timezone


class Tenant(TenantMixin):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    contact = models.CharField(max_length=15)
    owner_name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    trial_period_days = models.PositiveBigIntegerField(default=30)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    schema_name = models.CharField(max_length=100, unique=True, blank=True, null=True)  # Field for the schema name
    
    auto_created_schema = True
    auto_drop_schema = True 

    def generate_schema_name(self):
        schema_name = self.name.lower().replace(" ", "")  
        schema_name = re.sub(r'^[^a-zA-Z]', 'a', schema_name)  
        schema_name = re.sub(r'[^a-zA-Z0-9]', '', schema_name)
        unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        schema_name_with_suffix = f"{schema_name}{unique_suffix}"
        while Tenant.objects.filter(schema_name=schema_name_with_suffix).exists():
            unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            schema_name_with_suffix = f"{schema_name}{unique_suffix}"

        return schema_name_with_suffix

    def save(self, *args, **kwargs):
            
        if not self.schema_name:
            self.schema_name = self.generate_schema_name()
                # if not self.domain_url:
                #       self.domain_url = f"{self.schema_name}.streamway.com" 

        super().save(*args, **kwargs)


class Domain(DomainMixin):

    pass


class TenantBilling(models.Model):
    """
    Billing information for each tenant
    """
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='billing')
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    billing_email = models.EmailField()
    billing_name = models.CharField(max_length=200)
    per_user_rate = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)  # Default $10 per user
    billing_expiry = models.DateTimeField(null=True, blank=True)  
    is_active = models.BooleanField(default=True)
    last_billed_date = models.DateTimeField(blank=True, null=True)
    next_billing_date = models.DateTimeField(blank=True, null=True)
    last_billing_status = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Billing for {self.tenant.name}"
    
    def save(self, *args, **kwargs):
        # Create Stripe customer if doesn't exist
        if not self.stripe_customer_id:
            stripe.api_key = settings.STRIPE_SECRET_KEY  # ✅ This matches your settings

            customer = stripe.Customer.create(
                email=self.billing_email,
                name=self.billing_name,
                description=f"Customer for tenant: {self.tenant.name}"
            )
            self.stripe_customer_id = customer.id
            
        # Calculate next billing date if not set
        if not self.next_billing_date:

            # if self.tenant.created_on < timezone.now().date() - timedelta(days=30):
            #     self.next_billing_date = timezone.now()
            # else:
            #     # Set next billing date to 30 days after tenant creation
            #     creation_date = datetime.combine(self.tenant.created_on, datetime.min.time())
            #     aware_creation_date = timezone.make_aware(creation_date, timezone.get_current_timezone())
            #     print(creation_date)
            #     self.next_billing_date = aware_creation_date + timedelta(days=30)

            # if self.tenant.created_on < timezone.now().date() - timedelta(days=1):
            #     self.next_billing_date = timezone.now()
            # else:
            #     # Set next billing date to 30 days after tenant creation
            #     creation_date = datetime.combine(self.tenant.created_on, datetime.min.time())
            #     aware_creation_date = timezone.make_aware(creation_date, timezone.get_current_timezone())
            #     print(creation_date)
            #     self.next_billing_date = aware_creation_date + timedelta(minutes=10)



            if self.tenant.created_on < timezone.now().date() - timedelta(days=1):
                self.next_billing_date = timezone.now()
            else:
                # Use current time + 10 mins instead of 00:00 AM + 10 mins
                self.next_billing_date = timezone.now() + timedelta(minutes=5)

        
        super().save(*args, **kwargs)
    
    def calculate_bill_amount(self):
        """Calculate billing amount based on user count"""
        from django.db import connection
        from users.models import Employee
        
        connection.set_tenant(self.tenant)
        user_count = Employee.objects.all().count()+1
        print(user_count)
        amount = user_count * float(self.per_user_rate)
        return amount, user_count
    
    def create_billing_details(self):
        """Create billing details for Stripe"""
    
    def active_count_users(self):
        from django.db import connection
        from users.models import Employee
        
        connection.set_tenant(self.tenant)
        user_count = Employee.objects.all().count()+1
        print(user_count)
        return user_count
    


class Invoice(models.Model):
    """
    Invoice records for tenant billing
    """
    INVOICE_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    )
    
    tenant_billing = models.ForeignKey(TenantBilling, on_delete=models.CASCADE, related_name='invoices')
    stripe_invoice_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    user_count = models.IntegerField()  # Number of users at billing time
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    invoice_pdf_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"Invoice {self.id} for {self.tenant_billing.tenant.name} - {self.status}"

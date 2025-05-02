from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

from django.utils.translation import gettext_lazy as _
import re
import random
import string
import stripe
from django.conf import settings
from django_tenants.utils import schema_context


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
    tenant = models.OneToOneField("tenant.Tenant",on_delete=models.CASCADE,related_name='billing')
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    price_per_user = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Billing for {self.tenant.name}"
    
    def get_user_count(self):
        from users.models import Employee
        """Count the active users in this tenant"""
        with schema_context(self.tenant.schema_name):
            count = Employee.objects.all().count()+1
        
        return count
    
    def calculate_amount(self):
        """Calculate the billing amount based on user count"""
        user_count = self.get_user_count()
        return float(self.price_per_user) * user_count
    
    def create_stripe_customer(self):
        """Create a Stripe customer for this tenant if not exists"""
        if not self.stripe_customer_id:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            customer = stripe.Customer.create(
                name=self.tenant.name,
                email=self.tenant.email,
                description=f"Customer for tenant {self.tenant.name}"
            )
            self.stripe_customer_id = customer.id
            self.save()
        return self.stripe_customer_id

class BillingInvoice(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    )
    
    tenant_billing = models.ForeignKey(TenantBilling, on_delete=models.CASCADE, related_name='invoices')
    stripe_invoice_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    user_count = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    invoice_date = models.DateField()
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Invoice {self.id} - {self.tenant_billing.tenant.name}"

class TenantSMTPSettings(models.Model):
    tenant = models.OneToOneField("Tenant", on_delete=models.CASCADE)
    smtp_host = models.CharField(max_length=255, default="smtp.gmail.com")
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_username = models.EmailField()
    smtp_password = models.CharField(max_length=255)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)


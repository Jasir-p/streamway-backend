from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

from django.utils.translation import gettext_lazy as _
import re
import random
import string


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


class TenantSMTPSettings(models.Model):
    tenant = models.OneToOneField("Tenant", on_delete=models.CASCADE)
    smtp_host = models.CharField(max_length=255, default="smtp.gmail.com")
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_username = models.EmailField()
    smtp_password = models.CharField(max_length=255)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)


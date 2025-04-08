from django.contrib.auth.models import User
from django_tenants.signals import post_schema_sync
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password
from django_tenants.utils import schema_context

from django_tenants.models import TenantMixin
from .utlis.password_genarator import generate_password
import redis
import json

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0,
                                 decode_responses=True)


@receiver(post_schema_sync, sender=TenantMixin)
def create_tenant_owner(sender, **kwargs):
    """
    Creates a tenant owner when a new tenant schema is created and synced.
    This is triggered after the schema for the tenant is created.
    """

    tenant = kwargs['tenant']
    schema_name = tenant.schema_name
    print(f"Signal received for schema: {schema_name}")
    password = generate_password()
    email = tenant.email
    redis_key = f"password:{email}"
    redis_client.hmset(redis_key, {
    'generated_password': password
})


    
    # Hash the password securely
    password_hash = make_password(password)

    # Create the tenant owner in the public schema context
    with schema_context('public'): 
        User.objects.create(
          
            username=tenant.email,  
            password=password_hash,
            
        )
        print(f"Tenant owner created for tenant {schema_name} with username {tenant.email}.")

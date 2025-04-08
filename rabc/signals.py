from django_tenants.signals import post_schema_sync
from django.dispatch import receiver
from django_tenants.utils import schema_context
from Main_rbac.models import Permission
from .models import TenantPermission
from django_tenants.models import TenantMixin


@receiver(post_schema_sync, sender=TenantMixin)
def create_permission_for_tenant(sender, **kwargs):
    """This is for auto permission setting in each tenant schema
    after tenant creation."""
    
    # Access the tenant object
    tenant = kwargs['tenant']
    schema_name = tenant.schema_name
    print(f"Signal received for schema: {schema_name}")
    
    # Fetch all permissions from the public schema
    permissions = Permission.objects.all()
    
    # Create tenant permissions in the newly created tenant schema
    with schema_context(schema_name):
        for perm in permissions:
            TenantPermission.objects.get_or_create(
                name=perm.name,
                code_name=perm.code_name,
                module=perm.module,
                permission=perm,  
            )

    print(f"Permissions successfully added to tenant schema {schema_name}")

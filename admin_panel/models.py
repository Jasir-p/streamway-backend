from django.db import models
from tenant.models import Tenant


class AdminActivityLog(models.Model):
    tenant = models.ForeignKey(Tenant, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

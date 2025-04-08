from django.db import models
from tenant.models import Tenant


class Permission(models.Model):
    name = models.CharField(max_length=250)
    code_name = models.CharField(max_length=200)
    module = models.CharField(max_length=100)

    def __str__(self):
        return self.name


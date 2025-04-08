from django.db import models
from Main_rbac.models import Permission
from django.db.models import SET_NULL
from tenant.models import Tenant

# Create your models here.


class Role(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    parent_role = models.ForeignKey('self', null=True, blank=True, 
                                    on_delete=SET_NULL, related_name="children")
    
    def get_role_hierarchy(self, level=0):
        """ Recursively fetch roles as a nested dictionary """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "level": level,
            "children": [child.get_role_hierarchy(level=level+1) for child in self.children.all()]
        }

    def __str__(self):
        return self.name


class TenantPermission(models.Model):
    name = models.CharField(max_length=250)
    code_name = models.CharField(max_length=200)
    module = models.CharField(max_length=100)
    permission = models.ForeignKey("Main_rbac.Permission", on_delete=SET_NULL, 
                                   null=True, blank=True, default=None)


class RoleAcessPermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, 
                             related_name="role")
    Permission = models.ForeignKey(TenantPermission, on_delete=models.CASCADE, 
                                   related_name="tenantpermission")
    







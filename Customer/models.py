from django.db import models

from users.models import Employee





class Accounts(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('prospect', 'Prospect'),
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone_number = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    lead = models.ForeignKey(
        'leads.Leads', on_delete=models.SET_NULL, null=True, blank=True,
        related_name="lead_acount"
    )
    assigned_to = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True
    )
    assigned_by = models.ForeignKey(
    
       Employee, on_delete=models.SET_NULL, null=True, blank=True,
       related_name='assigned_acounts'

    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    custome_fields = models.JSONField(null=True, blank=True,default=None)


class Notes(models.Model):
    notes = models.TextField(blank=True)
    account = models.ForeignKey(Accounts,on_delete=models.CASCADE, null=True,blank=True)
    created_by = models.ForeignKey(
    
       Employee, on_delete=models.SET_NULL, null=True, blank=True,
       related_name='created_notes'

    )
    created_at = models.DateTimeField(auto_now_add=True)


class Contact(models.Model):
    STATUS_CHOICE = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),

    ]

    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone_number = models.CharField(max_length=20)
    assigned_to = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True
    )
    assigned_by = models.ForeignKey(
    
       Employee, on_delete=models.SET_NULL, null=True, blank=True,
       related_name='assigned_contacts'

    )
    status = models.CharField(
        max_length=100, choices=STATUS_CHOICE, default='active'
    )
    department = models.CharField(max_length=100, blank=True,null=True)
    is_primary_contact = models.BooleanField(default=False)
    account_id = models.ForeignKey(Accounts, on_delete=models.CASCADE, null=True,blank=True, related_name="contacts")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
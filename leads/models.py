from django.db import models
from users.models import Employee
import random
from django.db.models import SET_NULL
from Customer.models import Accounts


class LeadFormField(models.Model):
    field_name = models.CharField(max_length=255)
    field_type = models.CharField(max_length=255)
    is_required = models.BooleanField(default=False)
    validation_rules = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    options = models.JSONField(null=True, blank=True)


class WebForm(models.Model):
    web_id = models.CharField(
        
     max_length=8, unique=True, blank=True,
     primary_key=True, default=None
    )
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("follow_up", "Follow-up Scheduled"),
        ("negotiation", "Negotiation"),
        ("converted", "Converted"),
        ("lost", "Lost"),
    ]
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=255, choices=STATUS_CHOICES, default="new"
    )
    custome_fields = models.JSONField(null=True, blank=True)

    def generate_id(self):
        while True:
            unique_id = f"WE{random.randint(100000, 999999)}"
            if not WebForm.objects.filter(web_id=unique_id).exists():
                return unique_id
            
    def save(self, *args, **kwargs):
        if not self.web_id:
            self.web_id = self.generate_id()
        super(WebForm, self).save(*args, **kwargs)





class Leads(models.Model):
    lead_id = models.CharField(
      max_length=8, unique=True, blank=True,
      primary_key=True      
    )
    form_data = models.ForeignKey(WebForm, on_delete=SET_NULL, null=True, blank=True, related_name="leads")
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("follow_up", "Follow-up Scheduled"),
        ("negotiation", "Negotiation"),
        ("converted", "Converted"),
        ("lost", "Lost"),
    ]
    name = models.CharField(max_length=255)
    
    email = models.EmailField(max_length=255)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True)
    granted_by = models.ForeignKey(
     Employee, on_delete=models.CASCADE, related_name="granted_by", null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=255, choices=STATUS_CHOICES, default="new"
    )
    custome_fields = models.JSONField(null=True, blank=True)


    def generate_id(self):
        while True:
            unique_id = f"LE{random.randint(100000, 999999)}"
            if not Leads.objects.filter(lead_id=unique_id).exists():
                return unique_id
            
    def save(self, *args, **kwargs):
        if not self.lead_id:
            self.lead_id = self.generate_id()
        super().save(*args, **kwargs)
        



class LeadNotes(models.Model):
    notes = models.TextField(blank=True)
    lead = models.ForeignKey(Leads,on_delete=models.CASCADE, null=True,blank=True)
    created_by = models.ForeignKey(
    
       Employee, on_delete=models.SET_NULL, null=True, blank=True,
       related_name='created_lead_notes'

    )
    created_at = models.DateTimeField(auto_now_add=True)


class Deal(models.Model):
    deal_id = models.CharField(
      max_length=8, unique=True, blank=True,
      primary_key=True      
    )
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]

    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    STAGE_CHOICES = [
        ('qualification', 'Qualification'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('closed_lost', 'Closed Lost'),
        ('closed_won', 'Closed Won'),
        ('discovery', 'Discovery'),


    ]

    account_id = models.ForeignKey(Accounts, on_delete=models.CASCADE,default=None, related_name="deals")
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='new')
    stage = models.CharField(max_length=100, choices=STAGE_CHOICES, blank=True, null=True)
    expected_close_date = models.DateField()

    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)


    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def generate_id(self):
        while True:
            unique_id = f"D{random.randint(100000, 999999)}"
            if not Deal.objects.filter(deal_id=unique_id).exists():
                return unique_id
            
    def save(self, *args, **kwargs):
        if not self.deal_id:
            self.deal_id = self.generate_id()
        super(Deal, self).save(*args, **kwargs)

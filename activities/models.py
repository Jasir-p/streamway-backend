from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from users.models import Employee,Team
from leads.models import Leads
from Customer.models import Contact,Accounts




class Task(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('REVIEW', 'Review'),
        ('COMPLETED', 'Completed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()

    # Separate fields for Leads, Contacts, and Accounts
    lead = models.ForeignKey(Leads, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    account = models.ForeignKey(Accounts, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    is_team = models.BooleanField(default=False)
    assigned_to_employee = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_tasks'
    )
    assigned_to_team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='team_tasks'
    )
    assigned_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_by'
    )
    created_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_tasks'
    )
    
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=35, choices=STATUS_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    duedate = models.DateField(null=True, blank=True)
    attachment = models.FileField(
        upload_to='task_attachments/', default=None, null=True
    )
    
    def __str__(self):
        return self.title


class Email(models.Model):
    CATEGORY_CHOICES = [
        ('follow_up', 'Follow Up'),
        ('after_sale', 'After Sale'),
        ('leads', 'Leads'),
    ]
    sender = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='sent_emails',null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    to_lead = models.ForeignKey(Leads, on_delete=models.SET_NULL, related_name='emails', null=True, blank=True)
    to_contacts = models.ForeignKey(Contact, on_delete=models.SET_NULL, related_name='emails', null=True, blank=True)
    to_account = models.ForeignKey(Accounts, on_delete=models.SET_NULL, related_name='emails', null=True, blank=True)
    subject = models.CharField(max_length=200,null=True,blank=True)
    body = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

class Meeting(models.Model):
    status_choice = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField()
    duration = models.IntegerField(default=None)
    host = models.ForeignKey(
        Employee, on_delete=models.SET_NULL,
        related_name='host_meetings', null=True
    )
    status = models.CharField(max_length=20, choices=status_choice, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='created_meetings', null=True)
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)




    


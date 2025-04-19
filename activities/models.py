from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from users.models import Employee,Team
from leads.models import Leads
from Customer.models import Contact,Accounts


class Attachment(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/')
    file_name = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True)


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
        ('DONE', 'Done'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()

    # Separate fields for Leads, Contacts, and Accounts
    lead = models.ForeignKey(Leads, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    account = models.ForeignKey(Accounts, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')

    assigned_to_employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, null=True, blank=True,
        related_name='assigned_tasks'
    )
    assigned_to_team = models.ForeignKey(
        Team, on_delete=models.CASCADE, null=True, blank=True,
        related_name='team_tasks'
    )
    assigned_by = models.ForeignKey(
        Employee, on_delete=models.CASCADE, null=True, blank=True,
        related_name='created_tasks'
    )
    
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=35, choices=STATUS_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title



    


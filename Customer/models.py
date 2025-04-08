# from django.db import models
# from leads.models import Leads
# from users.models import Employee


# class Contact(models.Model):
#     STATUS_CHOICE = [
#         ('active', 'Active'),
#         ('inactive', 'Inactive'),
#         ('lost', 'Lost'),
#         ("follow_up", "Follow Up"),

#     ]

#     name = models.CharField(max_length=100)
#     email = models.EmailField(max_length=100)
#     phone_number = models.CharField(max_length=20)
#     lead = models.OneToOneField(
#         Leads, on_delete=models.CASCADE, null=True, blank=True
#     )
#     assigned_to = models.ForeignKey(
#         Employee, on_delete=models.CASCADE, null=True, blank=True
#     )
#     assigned_by = models.ForeignKey(
        
#        Employee, on_delete=models.CASCADE, null=True, blank=True,
#        related_name='assigned_contacts'
   
#     )
#     status = models.CharField(
#         max_length=100, choices=STATUS_CHOICE, default='active'
#     )
#     created_at = models.DateTimeField(auto_now_add=True)






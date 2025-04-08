from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Permission
from .utlis.permission_genarator import permisson_genarator


Predfind_Modules = ['Leads', 'Contacts', 'Meetings', 'Customer', 'Task', 
                    'Calls', 'Emails', 'Team']


@receiver(post_migrate)
def create_permission(sender,  **kwargs):
    if sender.name == 'Main_rbac':
        for module in Predfind_Modules:
            for perm in permisson_genarator(module):
                Permission.objects.get_or_create(
                    code_name=perm["codename"], name=perm["name"],
                    module=perm["module"]
                )



        

        


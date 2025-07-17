from django.db import models
from django.contrib.auth.hashers import make_password
from rabc.models import Role
from django.db.models import SET_NULL
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
# Create your models here.


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=15,null=True,blank=True)
    joined = models.DateField(default=timezone.now)  
    password = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    role = models.ForeignKey(Role, on_delete=SET_NULL, null=True, blank=True,
                             related_name="user")

    def __str__(self):
        return f"{self.name}({self.email})"
    

class Team (models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    team_lead = models.ForeignKey(Employee, on_delete=SET_NULL,
                                  null=True, related_name="team_lead")
    created_by = models.ForeignKey(User, on_delete=SET_NULL,
                                   null=True, blank=True, 
                                   related_name="created_team")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    members = models.ManyToManyField(Employee, through="TeamMembers", related_name="team_memberships")


class TeamMembers(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, 
                             related_name="team_members")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                 related_name="teams")
    joined_at = models.DateTimeField(auto_now_add=True)

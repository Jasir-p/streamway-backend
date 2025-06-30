from django.db import models
from users.models import Employee,Team

# Create your models here.
class ChatRoom(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE,blank=True, null=True)
    room_name = models.CharField(max_length=255, blank=True, null=True)
    is_group = models.BooleanField(default=False)
    participents = models.ManyToManyField(Employee, related_name='chat_rooms', blank=True,)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        if self.is_group and self.room_name:
            return f"{self.room_name} - Group Chat"
        return f"Private Chat - {self.participents.first().username}"
    

class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='sent_messages',blank=True,null=True)
    content = models.TextField()
    timestamp =  models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(Employee, related_name='read_messages', blank=True)


class Notifications(models.Model):
    user = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='notifications',blank=True,null=True)
    type = models.CharField(max_length=40)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_clear = models.BooleanField(default=False)


from  django.db.models.signals import post_save,post_delete
from  django.dispatch import receiver
from users.models import Team,TeamMembers
from .models import ChatRoom


@receiver(post_save, sender=Team)
def create_chat_room(sender, instance, created, **kwargs):
    if created:
        room=ChatRoom.objects.create(team=instance,room_name=instance.name,is_group=True)
        room.participents.add(instance.team_lead)

@receiver(post_save, sender=TeamMembers)
def add_member(sender, instance, created, **kwargs):
    if created:
        try:
            room = ChatRoom.objects.get(team__id=instance.team.id, is_group=True)
            room.participents.add(instance.employee)
        except ChatRoom.DoesNotExist:
            pass


        
@receiver(post_delete, sender=TeamMembers)
def remove_member(sender, instance, **kwargs):
    try:
        room = ChatRoom.objects.get(team=instance.team, is_group=True)
        room.participents.remove(instance.employee)
    except ChatRoom.DoesNotExist:
        pass
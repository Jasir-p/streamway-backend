from .models import ChatRoom
from users.models import Employee

def add_member_to_group(room_id, user):
    room = ChatRoom.objects.get(id=room_id)
    user = Employee.objects.filter(user__id =user.id).first()
    room.participents.add(user)

def remove_member_from_group(room_id, user):
    room = ChatRoom.objects.get(id=room_id)
    user = Employee.objects.filter(user__id =user.id).first()
    room.participents.remove(user)

def add_group(room_name):
    room = ChatRoom.objects.create(name=room_name,is_group=True)
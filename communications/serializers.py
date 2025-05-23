# chat/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatRoom, Message
from users.serializer import UserListViewSerializer


class MessageSerializer(serializers.ModelSerializer):
    sender = UserListViewSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'chat_room', 'sender', 'content', 'timestamp', 'read_by']

class ChatRoomMemberSerializer(serializers.ModelSerializer):
    user = UserListViewSerializer(read_only=True)
    
    # class Meta:
    #     model = ChatRoomMember
    #     fields = ['id', 'room', 'user', 'joined_at']

class ChatRoomSerializer(serializers.ModelSerializer):
    participents = UserListViewSerializer(read_only = True, many = True)

    
    class Meta:
        model = ChatRoom
        fields = ['id', 'room_name', 'created_at', 'participents']
    
    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-timestamp').first()
        if last_message:
            return MessageSerializer(last_message).data
        return None
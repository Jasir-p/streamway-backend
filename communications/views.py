# chat/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import ChatRoom, Message
from .serializers import (
   ChatRoomSerializer, 
    MessageSerializer, ChatRoomMemberSerializer
)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    # serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ChatRoom.objects.all()
        user_id = self.request.query_params.get("user")
        group_chat = self.request.query_params.get("group_chat")



        if group_chat is not None:
            # Convert "true"/"false" (strings) to boolean
            is_group_chat = group_chat.lower() == "true"

            queryset = queryset.filter(is_group=is_group_chat)


        if user_id:
            queryset = queryset.filter(participents__id=user_id)

        return queryset

    def perform_create(self, serializer):
        room = serializer.save()
        # Add creator as a member
        # ChatRoomMember.objects.create(room=room, user=self.request.user)

    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        room = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            # ChatRoomMember.objects.create(room=room, user=user)
            return Response({'status': 'member added'}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        room = self.get_object()
        messages = room.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only show messages from rooms the user is a member of
        return Message.objects.filter(room__members__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        message = self.get_object()
        message.is_read = True
        message.save()
        return Response({'status': 'message marked as read'})
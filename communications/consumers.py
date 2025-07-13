
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import connection
import logging
from .services import add_member_to_group,remove_member_from_group
from .models import Notifications
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            
            self.room_id = self.scope['url_route']['kwargs'].get('room_name', 'default')
                
            self.room_group_name = f"chat_{self.room_id}"

            self.tenant = self.scope.get("tenant", None)
            
            if self.tenant:

                await self.set_tenant_schema(self.tenant)
                tenant_schema_name = self.tenant.schema_name
                logger.info(f"WebSocket connected using tenant schema: {tenant_schema_name}")
            else:

                logger.warning("No tenant found in WebSocket scope, using public schema")
                tenant_schema_name = "public"
                


            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            

            user = self.scope.get('user')

            
            await self.accept()

        except Exception as e:

            logger.error(f"WebSocket connection error: {str(e)}")

            await self.accept()

            await self.close(code=4000)
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):

        if hasattr(self, 'tenant') and self.tenant:
            await self.set_tenant_schema(self.tenant)

       
        text_data_json = json.loads(text_data)
        type = text_data_json.get('type')
        if type == 'chat':
            message = text_data_json.get('message')

            msg=await self.save_message(message)

            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': msg
                }
            )
        elif type == 'addgroup':
            group_name = text_data_json.get('room_name')
            group = await self.add_group(group_name)

            await self.channel_layer.group_add(group_name, self.channel_name)
            await self.send(text_data=json.dumps({
                'type': 'group_created',
                'group_name': group
            }))
        elif type == 'removegroup':
            group_id = text_data_json.get('room_id')

            await self.remove_group(group_id)
           
            await self.channel_layer.group_send(
                   f"chat_{group_id}",
                    {
                        'type': 'group_deleted',
                        'group_id': group_id
                    }
                )



        elif type == 'adduser':
            user_id = text_data_json.get('user_id')
            group_id=text_data_json.get('group_id')
            await self.add_user(user_id, group_id)
            
            await self.channel_layer.group_send(
                    f"chat_{group_id}",
                    {
                        'type': 'user_added',
                        'user_id': user_id,
                        'group_id': group_id
                    }
                )


        elif type == 'removeuser':
            user_id = text_data_json.get('user_id')
            group_id=text_data_json.get('group_id')
            await self.remove_user(user_id, group_id)

            await self.channel_layer.group_send(
                    f"chat_{group_id}",
                    {
                        'type': 'user_removed',
                        'user_id': user_id,
                        'group_id': group_id
                    }
                )

        
        
        
    
    async def chat_message(self, event):

        if hasattr(self, 'tenant') and self.tenant:
            await self.set_tenant_schema(self.tenant)

            
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': message
        }))
    
    async def group_created(self, event):
        if hasattr(self, 'tenant') and self.tenant:
            await self.set_tenant_schema(self.tenant)

        """Handle group creation broadcast"""
        group_data = event['group_data']
        await self.send(text_data=json.dumps({
            'type': 'group_created',
            'group': group_data
        }))
    async def group_deleted(self, event):
        if hasattr(self, 'tenant') and self.tenant:
            await self.set_tenant_schema(self.tenant)
        await self.send(text_data=json.dumps({
            'type': 'group_deleted',
            'group_id': event.get('group_id')
        }))
    async def user_added(self, event):
        if hasattr(self, 'tenant') and self.tenant:
            await self.set_tenant_schema(self.tenant)
        await self.send(text_data=json.dumps({
            'type': 'user_added',
            'user_id': event.get('user_id'),
            'group_id': event.get('group_id')
        }))
    async def user_removed(self, event):
        if hasattr(self, 'tenant') and self.tenant:
            await self.set_tenant_schema(self.tenant)
        await self.send(text_data=json.dumps({
            'type': 'user_removed',
            'user_id': event.get('user_id'),
            'group_id': event.get('group_id')
        }))
    

    @database_sync_to_async
    def set_tenant_schema(self, tenant):
        """Set the DB connection to use the specified tenant schema"""

        connection.set_tenant(tenant)
        return True

    @database_sync_to_async
    def save_message(self, message_content):
        # We need to import here to avoid circular imports
        from users.models import Employee
        from .models import ChatRoom, Message 
        from.serializers import MessageSerializer
        
        try:
            user_instance = self.scope['user']

            if not user_instance.is_authenticated:

                return False

            
            user = Employee.objects.filter(user__id=user_instance.id).first()

           


            room = ChatRoom.objects.get(id=self.room_id)

            
            msag=Message.objects.create(
                chat_room=room,
                sender=user if user else None,
                content=message_content
            )
            serializer = MessageSerializer(msag)

            return serializer.data
        except Exception as e:

            logger.error(f"Error saving message: {str(e)}")
            return False
    @database_sync_to_async
    def add_group(self,group_name):
        from .models import ChatRoom, Message 
        from .serializers import ChatRoomSerializer
        if group_name:
            group, created = ChatRoom.objects.get_or_create(room_name=group_name,is_group=True)
            return ChatRoomSerializer(group).data
        return None
    @database_sync_to_async
    def remove_group(self,group_id):
        from .models import ChatRoom, Message
        if group_id:
            group = ChatRoom.objects.get(id=group_id)
            group.delete()
            return True
        return False
    
    @database_sync_to_async
    def add_user(self,user_id,group_id,):
        from .models import ChatRoom
        from users.models import Employee

        try:
            room = ChatRoom.objects.get(id=group_id)
        except ChatRoom.DoesNotExist:

            return 

        try:
            user = Employee.objects.get(id=user_id)
        except Employee.DoesNotExist:

            return

        room.participents.add(user)
    
    @database_sync_to_async
    def remove_user(self,user_id,group_id):
        from .models import ChatRoom
        from users.models import Employee
        try:
            room = ChatRoom.objects.get(id=group_id)
        except ChatRoom.DoesNotExist:
                pass
        
        try:
            user = Employee.objects.get(id=user_id)
        except Employee.DoesNotExist:
            pass

        room.participents.remove(user)
    

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import connection
from .serializers import NotificationSerializer
from .models import Notifications  
from users.models import Employee

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.tenant = self.scope.get("tenant", None)
        self.user = self.scope.get('user')

        # Set tenant schema
        if self.tenant:
            await self.set_tenant_schema(self.tenant)
            tenant_schema_name = self.tenant.schema_name
            logger.info(f"WebSocket connected using tenant schema: {tenant_schema_name}")
        else:
            logger.warning("No tenant found in WebSocket scope, using public schema")
            tenant_schema_name = "public"
        


        # Check user authentication
        if not self.user or not self.user.is_authenticated:
            logger.warning("User is not authenticated, rejecting WebSocket connection")
            await self.close()
            return


        await self.accept()

        self.group_name = f"user-{self.user.id}"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        logger.info(f"Added consumer to group: {self.group_name}")


        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "user.notification",
                "message": "New notification"
            }
        )

    async def disconnect(self, close_code):

        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"Removed consumer from group: {self.group_name}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get("type")

        if event_type == "mark_as_read":
            notification_ids = data.get("notification_ids", [])
            await self.mark_notifications_as_read(notification_ids)

    async def user_notification(self, event):
        logger.info(f"Received user_notification event: {event}")
        try:
            notifications = await self.get_user_notifications()
            # print(f"Notifications for user {self.user.id}: {notifications}")
            await self.send(text_data=json.dumps(notifications))
        except Exception as e:
            logger.error(f"Error in user_notification: {str(e)}")
            await self.send(text_data=json.dumps({"error": str(e)}))

    @database_sync_to_async
    def set_tenant_schema(self, tenant):
        """Set the DB connection to use the specified tenant schema"""
        try:

            connection.set_tenant(tenant)
            return True
        except Exception as e:
            logger.error(f"Failed to set tenant schema: {str(e)}")
            raise

    @database_sync_to_async
    def get_user_notifications(self):
        try:
            user = self.scope.get('user')
            if Employee.objects.filter(user=user).exists():

                notifications = Notifications.objects.filter(
                    user__user__id=user.id,
                    is_read=False,
                    is_clear=False
                )
            else:
                notifications = Notifications.objects.filter(
                    user=None,
                    is_read=False,
                    is_clear=False
                )
            serializer = NotificationSerializer(notifications, many=True)
            # print(f"Serialized notifications: {serializer.data}")
            return serializer.data
        except Exception as e:
            logger.error(f"Error fetching notifications: {str(e)}")
            raise
    @database_sync_to_async
    def mark_notifications_as_read(self, notification_ids):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            return
        if Employee.objects.filter(user=user).exists():
            Notifications.objects.filter(
                id__in=notification_ids,
                user__user__id=user.id  
            ).update(is_read=True)
        else:
            Notifications.objects.filter(
                id__in=notification_ids,
                user=None 
            ).update(is_read=True)











        
        
    
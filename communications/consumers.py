
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
                
            print(f"Using tenant schema: {tenant_schema_name}")

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            

            user = self.scope.get('user')
            print(f"User connecting: {user}")
            
            await self.accept()
            print(f"WebSocket Connected to {self.room_group_name} (Room ID: {self.room_id})")
        except Exception as e:
            print(f" Error in connect: {str(e)}")
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
        print(" receive() method called")
        if hasattr(self, 'tenant') and self.tenant:
            await self.set_tenant_schema(self.tenant)
            print(f" Reset tenant schema to: {self.tenant.schema_name}")
       
        text_data_json = json.loads(text_data)
        type = text_data_json.get('type')
        if type == 'chat':
            message = text_data_json.get('message')
            print("📩 Received message:", message)
            msg=await self.save_message(message)
            print(msg)
            
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
            print(f"👥 Adding group: {group_name}")
            await self.channel_layer.group_add(group_name, self.channel_name)
            await self.send(text_data=json.dumps({
                'type': 'group_created',
                'group_name': group
            }))
        elif type == 'removegroup':
            group_id = text_data_json.get('room_id')
            print(f"🚫 Removing group: {group_id}"
                  )
            await self.remove_group(group_id)
            # await self.channel_layer.group_discard(group_id, self.channel_name)


        elif type == 'adduser':
            user_id = text_data_json.get('user_id')
            group_id=text_data_json.get('group_id')
            await self.add_user(user_id, group_id)

        elif type == 'removeuser':
            user_id = text_data_json.get('user_id')
            group_id=text_data_json.get('group_id')
            await self.remove_user(user_id, group_id)

        
        
        
    
    async def chat_message(self, event):

        if hasattr(self, 'tenant') and self.tenant:
            await self.set_tenant_schema(self.tenant)
            print(f"🔄 Reset tenant schema to: {self.tenant.schema_name}")
            
        message = event['message']
        print(message)
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': message
        }))
    
    async def group_created(self, event):
        if hasattr(self, 'tenant') and self.tenant:
            await self.set_tenant_schema(self.tenant)
            print(f"🔄 Reset tenant schema to: {self.tenant.schema_name}")
        """Handle group creation broadcast"""
        group_data = event['group_data']
        await self.send(text_data=json.dumps({
            'type': 'group_created',
            'group': group_data
        }))

    @database_sync_to_async
    def set_tenant_schema(self, tenant):
        """Set the DB connection to use the specified tenant schema"""
        print(f"Setting tenant schema to: {tenant.schema_name}")
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
            print("User:", user_instance)
            if not user_instance.is_authenticated:
                print("Unauthenticated user. Message not saved.")
                return False

            
            user = Employee.objects.filter(user__id=user_instance.id).first()
            print("Employee user:", user)
           

            print(f"Looking for room with ID: {self.room_id}")
            room = ChatRoom.objects.get(id=self.room_id)
            print(f"Found room: {room}")
            
            msag=Message.objects.create(
                chat_room=room,
                sender=user if user else None,
                content=message_content
            )
            serializer = MessageSerializer(msag)
            print("Message saved successfully")
            return serializer.data
        except Exception as e:
            print(f"Error saving message: {str(e)}")
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
            print(f"ChatRoom with id {group_id} does not exist.")
            return 

        try:
            user = Employee.objects.get(id=user_id)
        except Employee.DoesNotExist:
            print(f"Employee with id {user_id} does not exist.")
            return

        room.participents.add(user)
    
    @database_sync_to_async
    def remove_user(self,user_id,group_id):
        from .models import ChatRoom
        from users.models import Employee
        try:
            room = ChatRoom.objects.get(id=group_id)
        except ChatRoom.DoesNotExist:
                print(f"ChatRoom with id {group_id} does not exist.")
        
        try:
            user = Employee.objects.get(id=user_id)
        except Employee.DoesNotExist:
            print(f"Employee with id {user_id} does not exist.")

        room.participents.remove(user)
    

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import connection
from .serializers import NotificationSerializer
from .models import Notifications  # Ensure this import is correct

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
        
        print(f"Using tenant schema: {tenant_schema_name}")

        # Check user authentication
        if not self.user or not self.user.is_authenticated:
            logger.warning("User is not authenticated, rejecting WebSocket connection")
            await self.close()
            return

        print(f"CurrentUser: {self.user}, ID: {self.user.id}")
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
        print(f"Disconnected with code: {close_code}")
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"Removed consumer from group: {self.group_name}")

    async def user_notification(self, event):
        logger.info(f"Received user_notification event: {event}")
        try:
            notifications = await self.get_user_notifications()
            print(f"Notifications for user {self.user.id}: {notifications}")
            await self.send(text_data=json.dumps(notifications))
        except Exception as e:
            logger.error(f"Error in user_notification: {str(e)}")
            await self.send(text_data=json.dumps({"error": str(e)}))

    @database_sync_to_async
    def set_tenant_schema(self, tenant):
        """Set the DB connection to use the specified tenant schema"""
        try:
            print(f"Setting tenant schema to: {tenant.schema_name}")
            connection.set_tenant(tenant)
            return True
        except Exception as e:
            logger.error(f"Failed to set tenant schema: {str(e)}")
            raise

    @database_sync_to_async
    def get_user_notifications(self):
        try:
            user = self.scope.get('user')
            print(f"Fetching notifications for user ID: {user.id}")
            # Verify the model relationship (user__user__id seems unusual)
            notifications = Notifications.objects.filter(
                user__user__id=user.id,
                is_read=False,
                is_clear=False
            )
            serializer = NotificationSerializer(notifications, many=True)
            print(f"Serialized notifications: {serializer.data}")
            return serializer.data
        except Exception as e:
            logger.error(f"Error fetching notifications: {str(e)}")
            raise











        
        
    
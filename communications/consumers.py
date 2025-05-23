
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Check if 'room_id' exists in kwargs
            if 'room_id' in self.scope['url_route']['kwargs']:
                self.room_id = self.scope['url_route']['kwargs']['room_id']
            else:
                # Fallback to 'room_name' if it exists
                self.room_id = self.scope['url_route']['kwargs'].get('room_name', 'default')
                
            self.room_group_name = f"chat_{self.room_id}"
            
            # Get tenant from scope (set by our middleware)
            self.tenant = self.scope.get("tenant", None)
            
            if self.tenant:
                # Set the connection to use this tenant's schema
                await self.set_tenant_schema(self.tenant)
                tenant_schema_name = self.tenant.schema_name
                logger.info(f"WebSocket connected using tenant schema: {tenant_schema_name}")
            else:
                # If no tenant is found, log warning but continue with public schema
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
            print(f"✅ WebSocket Connected to {self.room_group_name} (Room ID: {self.room_id})")
        except Exception as e:
            print(f"❌ Error in connect: {str(e)}")
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
        print("🟡 receive() method called")
        if hasattr(self, 'tenant') and self.tenant:
            await self.set_tenant_schema(self.tenant)
            print(f"🔄 Reset tenant schema to: {self.tenant.schema_name}")
       
        text_data_json = json.loads(text_data)
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
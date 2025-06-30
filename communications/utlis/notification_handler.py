from communications.models import Notifications
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def notification_set(type, message, user=None):
    print("id",user.id)
    # Save the notification
    save =  Notifications.objects.create(type=type, message=message, user=user)

    # Send to WebSocket group
    channel_layer = get_channel_layer()
    user_id = user.user.id 
    print("user",user_id)
    async_to_sync( channel_layer.group_send)(
        f"user-{user_id}",  
        {
            "type": "user.notification", 
            "data": {
                "id": save.id,
                "type": type,
                "message": message,
            }
        }
    )

from communications.models import Notifications
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
from django.contrib.auth import get_user_model


logger = logging.getLogger(__name__)
User=get_user_model()



def notification_set(type, message, user=None,tenant=None):
    
    if user:
        user_id=user.user.id
    elif tenant:
        user_id=User.objects.get(username=tenant.email).id
    else:
        return
        
    saved = Notifications.objects.create(
        type=type,
        message=message,
        user=user
    )
    # Now safely send WebSocket (pure async section)
    try:
        channel_layer = get_channel_layer()
        if channel_layer is not None:
            # Prepare message data
            data = {
                "type": "user.notification",
                "data": {
                    "id": saved.id,
                    "type": type,
                    "message": message,
                }
            }

            async_to_sync(channel_layer.group_send)(f"user-{user_id}", data)

    except Exception as e:
        logger.error(f'"{str(e)}"')
 

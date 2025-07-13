from communications.models import Notifications
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

# def notification_set(type, message, user=None):
#     print("id",user.id)
#     # Save the notification
#     save =  Notifications.objects.create(type=type, message=message, user=user)

#     # Send to WebSocket group
#     channel_layer = get_channel_layer()
#     user_id = user.user.id 
#     print("user",user_id)
#     async_to_sync( channel_layer.group_send)(
#         f"user-{user_id}",  
#         {
#             "type": "user.notification", 
#             "data": {
#                 "id": save.id,
#                 "type": type,
#                 "message": message,
#             }
#         }
#     )



def notification_set(type, message, user=None):
    # if not user:
    #     return

    print("➡️ Creating notification for user", user.id)

    # Save notification to DB (this is a sync DB operation)
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

            # Only use async call after DB operations
            user_id = user.user.id
            async_to_sync(channel_layer.group_send)(f"user-{user_id}", data)

    except Exception as e:
        logger.error(f'"{str(e)}"')
 

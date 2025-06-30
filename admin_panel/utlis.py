
# from .tasks import log_to_redis_task

# def dispatch_activity_event(user_id, tenant_id, model_name, object_id, action, is_admin=False):
#     log_to_redis_task.delay(
#         user_id=user_id,
#         tenant_id=tenant_id,
#         model_name=model_name,
#         object_id=object_id,
#         action=action,
#         is_admin=is_admin,
#     )
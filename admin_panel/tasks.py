# from celery import shared_task
# import redis
# import json
# from datetime import datetime

# redis_client = redis.StrictRedis(host='redis', port=6379, db=0,
#                                  decode_responses=True)

# @shared_task
# def log_to_redis_task(user_id, tenant_id, model_name, object_id, action, is_admin=False):
#     timestamp = datetime.utcnow().isoformat()
#     key = (
#         f"activity:admin:{user_id}:{model_name}:{object_id}"
#         if is_admin
#         else f"activity:tenant:{tenant_id}:{user_id}:{model_name}:{object_id}"
#     )

#     value = {
#         "action": action,
#         "model": model_name,
#         "object_id": object_id,
#         "timestamp": timestamp,
#         "user_id": user_id,
#         "tenant_id": tenant_id if not is_admin else None,
#     }

#     redis_client.set(key, json.dumps(value), ex=60 * 60 * 24 * 15)  # 15 days
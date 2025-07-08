from celery import shared_task
import redis
import json
from datetime import datetime

redis_client = redis.StrictRedis(host='redis', port=6379, db=0,
                                 decode_responses=True)

@shared_task
def log_user_activity_task(user_id, action, max_logs=50):
    key = "active_logs"
    ttl_seconds = 60 * 60 * 48  

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "name": user_id,
        "action": action,
        "timestamp": timestamp,
    }
    logs_json = redis_client.get(key)
    logs = json.loads(logs_json) if logs_json else []


    logs.insert(0, log_entry)


    logs = logs[:max_logs]

    if not redis_client.exists(key):
        redis_client.set(key, json.dumps(logs))
        redis_client.expire(key, ttl_seconds)
    else:
        redis_client.set(key, json.dumps(logs))
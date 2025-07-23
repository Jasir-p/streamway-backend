import random
import redis
from datetime import datetime,timedelta

redis_client = redis.StrictRedis(host='redis', port=6379, db=0,
                                 decode_responses=True)

OTP_PREFIX = "otp_"
MAX_RESEND_COUNT = 10
OTP_EXPIRE_SECONDS = 120


def generate_otp(email, length=6):
    """Generate a numeric OTP of a specified length."""
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    key = f"{OTP_PREFIX}{email}"

    redis_client.hmset(key, {
        'otp': otp,
        "created_at": datetime.now().isoformat(),
        "resend_count": 0
    })
    expiry_minutes = 2
    redis_client.expire(key, OTP_EXPIRE_SECONDS)
    return otp, expiry_minutes


def validate_otp(email, otp):
    """
    OTP validation method
    """
    key = f"{OTP_PREFIX}{email}"

    otp_data = redis_client.hgetall(key)

    if not otp_data:
         return False, "OTP not found"
    otp_get = otp_data.get("otp")
    created_at = otp_data.get("created_at")
    try:
        created_time = datetime.fromisoformat(created_at)
    except ValueError:
        return False, "Invalid created_at format"
    
    if datetime.now() > (created_time+timedelta(seconds=OTP_EXPIRE_SECONDS)):
        return False, "OTP expired"
    if otp_get != otp:
        return False, "Invalid OTP"
    
    redis_client.delete(key)

    return True, "OTP is valid"


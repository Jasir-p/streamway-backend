from users.models import Employee


def get_user(user_id):
    if user_id:
        return Employee.objects.get(id=user_id)
    return None
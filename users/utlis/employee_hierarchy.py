from django.db.models import Q, Subquery
from users.models import Employee

def get_employee_and_subordinates_ids(userid):
    return Employee.objects.filter(
        Q(id=userid) |
        Q(role__parent_role=Subquery(
            Employee.objects.filter(id=userid).values("role")[:1]
        ))
    ).values_list("id", flat=True)

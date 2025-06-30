from collections import defaultdict
from leads.models import Leads,Deal

from users.models import Employee
from users.utlis.employee_hierarchy import get_employee_and_subordinates_ids

def get_lead_analytics(user_id,subordinates,leads):
    if user_id is None:
        return []

    stats = {
        "own_leads": 0,
        "subordinate_leads": 0,
        "total_leads": 0
    }

    for lead in leads:
        if not lead.employee:
            continue
        if lead.status.lower() == "converted":
            stats["total_leads"] += 1
            if lead.employee.id == user_id:
                stats["own_leads"] += 1
            elif lead.employee.id in subordinates:
                stats["subordinate_leads"] += 1

    return stats



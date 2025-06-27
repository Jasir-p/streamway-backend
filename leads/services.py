from .models import Leads, Deal
from django.db.models import Count, Max

def get_lead_status_summary(employee_ids=None):
    queryset = Leads.objects.all()
    if employee_ids:
        queryset = queryset.filter(employee_id__in=employee_ids)
    
    return queryset.values('status','created_at')
def get_deal_status_summary(employee_ids=None):
    queryset = Deal.objects.all()
    if employee_ids:
        queryset = queryset.filter(owner__in=employee_ids)

    return queryset.values('deal_id', 'stage', 'amount', 'created_at')  # add more fields if needed


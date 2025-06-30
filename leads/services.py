from .models import Leads, Deal
from django.db.models import Count, Max
from tenant_panel.utils.applay_date_filter import apply_date_filter

def get_lead_status_summary(filter_type, start_date=None, end_date=None, employee_ids=None):
    queryset = Leads.objects.all()
    if employee_ids:
        queryset = queryset.filter(employee_id__in=employee_ids)
    queryset = apply_date_filter(queryset, filter_type, start_date, end_date)
    return queryset.values('status', 'created_at')


def get_deal_status_summary(filter_type, start_date=None, end_date=None, employee_ids=None):
    queryset = Deal.objects.all()
    if employee_ids:
        queryset = queryset.filter(owner__in=employee_ids)
    queryset = apply_date_filter(queryset, filter_type, start_date, end_date)
    return queryset.values('deal_id', 'stage', 'amount', 'created_at')
  # add more fields if needed


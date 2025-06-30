from datetime import datetime, timedelta
from django.utils import timezone

def apply_date_filter(queryset, filter_type, start_date=None, end_date=None):
    today = timezone.now().date()
    if filter_type == 'today':
        return queryset.filter(created_at__date=today)
    if filter_type == 'week':
        return queryset.filter(created_at__date__gte=today - timedelta(days=7))
    if filter_type == "month":
        return queryset.filter(created_at__month=today.month, created_at__year=today.year)
    
    elif filter_type in ['last_month', 'last-month']:
        last_month = today - timedelta(days=today.day + 1)
        return queryset.filter(created_at__month=last_month.month, created_at__year=last_month.year)

    elif filter_type == "year":
        return queryset.filter(created_at__year=today.year)

    elif filter_type == "custom" and start_date and end_date:
        return queryset.filter(created_at__date__range=[start_date, end_date])
    
    return queryset  # default (no filter)

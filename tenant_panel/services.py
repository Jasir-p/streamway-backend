from collections import defaultdict
from leads.models import Leads,Deal
from activities.models import Task,Meeting
from users.models import Employee,Team
from Customer.models import Accounts
from users.utlis.employee_hierarchy import get_employee_and_subordinates_ids
from .utils.lead_analytics import get_lead_analytics
from .utils.deal_analytics import get_deal_stats
from .utils.task_analytics import get_task_stats
from .utils.meeting_analytics import get_meeting_stats
from.utils.team_analytics import get_team_stats
from .utils.applay_date_filter import apply_date_filter
from.utils.accounts_analytics import get_accounts_stats
from django.db.models import Count,Sum


def get_analytics(user_id,filter_type,start_date,end_date):
    if user_id is None:
        return []

    all_ids = get_employee_and_subordinates_ids(user_id)
    subordinates = [eid for eid in all_ids if eid != user_id]
    current_user = Employee.objects.get(id=user_id)

    leads = apply_date_filter(Leads.objects.filter(employee__in=all_ids),filter_type,start_date,end_date)
    deals = apply_date_filter(Deal.objects.filter(owner__in=all_ids),filter_type,start_date,end_date)
    tasks = apply_date_filter(Task.objects.filter(assigned_to_employee__in=all_ids),filter_type,start_date,end_date)
    meetings = apply_date_filter(Meeting.objects.filter(host__in=all_ids),filter_type,start_date,end_date)
    accounts = apply_date_filter(Accounts.objects.filter(assigned_to__in=all_ids),filter_type,start_date,end_date)


    lead_stats =get_lead_analytics(user_id,subordinates,leads)
    deal_stats = get_deal_stats(user_id,subordinates,deals)
    task_stats = get_task_stats(user_id,subordinates,tasks)
    meeting_stats = get_meeting_stats(user_id,subordinates,meetings)
    account_stats = get_accounts_stats(user_id,subordinates,accounts)


    result = {
        "employee_id": user_id,
        "employee_name": current_user.name,
        'empolyee_role':current_user.role.name,
        "lead_stats": lead_stats,
        "deal_stats": deal_stats,
        "task_stats": task_stats,
        "meeting_stats": meeting_stats,
        "account_stats": account_stats
    }

    
        

    return result

def get_teams_analytics(team,filter_type,start_date,end_date):
    if team is None:
        return []

    tasks=apply_date_filter(Task.objects.filter(assigned_to_team=team.id),filter_type,start_date,end_date)
    team_stats= get_team_stats(team.id,tasks)

    result = {
        "team_id": team.id,
        "team_name":team.name,
        "team_stats": team_stats
    }
    return result

def get_tenants_analytics(filter_type,start_date,end_date):
    leads= apply_date_filter(Leads.objects.all().values('status','created_at','source'), filter_type,start_date,end_date)
    deals = apply_date_filter(Deal.objects.all().values('stage','created_at','amount'), filter_type, start_date, end_date)
    accounts = apply_date_filter(Accounts.objects.all().values('status'), filter_type, start_date, end_date)
    leads={
        'total_leads' : leads.count(),
        'converted_leads':len(leads.filter(status="converted")),
        'lost_leads':leads.filter(status="lost").count(),
        'lead_source': leads.values('source').annotate(count=Count('source')).order_by('-count'),
    }
    deals = {
        'total_deals': deals.count(),
        'converted_deals': len(deals.filter(stage="closed_won")),
        'lost_deals': deals.filter(stage="closed_lost").count(),
        'deal_value':deals.filter(stage='closed_won').aggregate(total=Sum('amount'))['total'] or 0,
    }
    accounts = {
        'total_accounts': accounts.count(),
        'active_accounts': accounts.filter(status="active").count(),
    }
    results = {
        'leads':leads,
        'deals':deals,
        'accounts':accounts
    }

    return results


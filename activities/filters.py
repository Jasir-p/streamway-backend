from django_filters import rest_framework as filters
from django.db import models
from .models import Meeting,Task,Email
from django.utils import timezone
from datetime import  timedelta

class MeetingFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=Meeting.status_choice)
    search = filters.CharFilter(method='filter_search')
    class Meta:
        model = Meeting
        fields = ['status']

    def filter_search(self, queryset, name, value):
        value = value.strip()
        if value:
            return queryset.filter(models.Q(title__istartswith=value)|
                                   models.Q(contact__name__istartswith=value)|
                                   models.Q(host__name__istartswith=value))
            
        return queryset
    

class TaskFilter(filters.FilterSet):
    search = filters.CharFilter(method='filter_search')
    status = filters.ChoiceFilter(choices=Task.STATUS_CHOICES)
    priority = filters.ChoiceFilter(choices=Task.PRIORITY_CHOICES)

    class Meta:
        model = Task
        fields = ['status','priority']

    def filter_search(self, queryset, name, value):
        value = value.strip()
        if value:
            return queryset.filter(models.Q(title__istartswith=value)|
                                   models.Q(lead__name__istartswith=value)|
                                   models.Q(assigned_to_employee__name__istartswith=value)|
                                   models.Q(assigned_to_team__name__istartswith=value)|
                                   models.Q(contact__name__istartswith=value)|
                                   models.Q(account__name__istartswith=value))
        return queryset



class EmailFilter(filters.FilterSet):
    DATE_CHOICES = [
    ('today', 'Today'),
    ('week', 'This Week'),
    ('month', 'This Month'),
    ('last_month', 'Last Month'),
]
    search = filters.CharFilter(method='filter_search')
    status = filters.BooleanFilter(field_name ='is_sent')
    date_range = filters.ChoiceFilter(choices=DATE_CHOICES,method='filter_date_range')
    start_date = filters.DateFilter(field_name="sent_at", lookup_expr='gte')
    end_date = filters.DateFilter(field_name="sent_at", lookup_expr='lte')
    category = filters.ChoiceFilter(choices=Email.CATEGORY_CHOICES,field_name="category")

    class Meta:
        model = Email
        fields = ['is_sent']

    def filter_search(self, queryset, name, value):
        value = value.strip()
        if value:
            return queryset.filter(
                models.Q(sender__name__istartswith=value)|
                models.Q(to_lead__name__istartswith=value)|
                models.Q(to_contacts__name__istartswith=value)|
                models.Q(to_account__name__istartswith=value)|
                models.Q(recipient_name__istartswith=value)|
                models.Q(recipient_email__istartswith=value)|
                models.Q(to_lead__email__istartswith=value)|
                models.Q(to_contacts__email__istartswith=value)|
                models.Q(to_account__email__istartswith=value))
        
        return queryset
    
    def filter_date_range(self, queryset, name, value):
        today = timezone.now().date()


        if value=='today':
            return queryset.filter(sent_at__date=today)
        
        if value =='week':
            return queryset.filter(sent_at__date__gte=today-timedelta(days=7))

        
        if value=='month':
            return queryset.filter(sent_at__date__month=today.month, sent_at__date__year=today.year)
        
        if value =='last_month':
            last_month = today - timedelta(days=today.day + 1)
            return queryset.filter(sent_at__date__month=last_month.month, sent_at__date__year =last_month.year)
        
        return queryset
    

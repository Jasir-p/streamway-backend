from django_filters import rest_framework as filters
from django.db import models
from .models import Leads,Deal,WebForm

class LeadFilter(filters.FilterSet):

    search = filters.CharFilter(method='filter_search')
    
    status = filters.ChoiceFilter(choices=Leads.STATUS_CHOICES)
    source = filters.ChoiceFilter(choices=Leads.SOURCE_CHOICES)
    
    
    class Meta:
        model = Leads
        fields = ['status', 'source']
    
    def filter_search(self, queryset, name, value):
        """
        Custom search filter that searches across multiple fields
        """
        value = value.strip()
        if value:
            return queryset.filter(
                models.Q(name__istartswith=value) |
                models.Q(email__istartswith=value) |
                models.Q(location__istartswith=value)|
                models.Q(employee__name__istartswith=value)
            )
        return queryset
    

class DealFilter(filters.FilterSet):
    search = filters.CharFilter(method='filter_search')
    status = filters.ChoiceFilter(choices=Deal.STATUS_CHOICES)
    stage = filters.ChoiceFilter(choices=Deal.STAGE_CHOICES)
    priority = filters.ChoiceFilter(choices=Deal.PRIORITY_CHOICES)


    class Meta:
        model = Deal
        fields = ['status', 'stage', 'priority']

    
    def filter_search(self, queryset, name, value):
        """ Custom search filter that searches across multiple fields"""
        value = value.strip()
        if not value:
            return queryset
        amount_filter = models.Q()
        try:
            amount_val = float(value)
            amount_filter=models.Q(amount__gte=amount_val)
        except:
            pass
        
        if value:
            return queryset.filter(
                models.Q(title__istartswith=value) | 
                models.Q(owner__name__istartswith=value) |
                models.Q(account_id__name__istartswith=value)|
            models.Q(account_id__email__istartswith=value)|
            amount_filter
        )
        
    

class EnquiryFilter(filters.FilterSet):
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = WebForm
        fields = [] 

    
    def filter_search(self, queryset, name, value):
        """ Custom search filter that searches across multiple fields"""
        value = value.strip()
        if value:
            return queryset.filter(
                 models.Q(name__istartswith=value) |
                models.Q(email__istartswith=value) |
                models.Q(location__istartswith=value)
            )
        return queryset




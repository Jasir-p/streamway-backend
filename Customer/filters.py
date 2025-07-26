from django_filters import rest_framework as filters
from .models import Accounts,Contact
from django.db import models



class AccountFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=Accounts.STATUS_CHOICES)
    search = filters.CharFilter(method='filter_search')
    class Meta:
        model = Accounts
        fields = ['status','search']

    def filter_search(self, queryset, name, value):
            value = value.strip()
            if value:
                return queryset.filter(
                    models.Q(name__istartswith=value)|
                    models.Q(email__istartswith=value)|
                    models.Q(assigned_to__name__istartswith=value)|
                    models.Q(phone_number__istartswith=value))
            return queryset
    

class ContactFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=Contact.STATUS_CHOICE)
    search = filters.CharFilter(method='filter_search')
    class Meta:
         model = Contact
         fields = ['status','search']
    
    def filter_search(self, queryset, name, value):
        value = value.strip()
        if value:
              return queryset.filter(
                   models.Q(name__istartswith=value)|
                   models.Q(email__istartswith=value)|
                   models.Q(phone_number__istartswith=value)|
                   models.Q(assigned_to__name__istartswith=value))
        
        return queryset


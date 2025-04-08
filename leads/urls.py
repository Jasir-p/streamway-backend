from django.urls import path
from .views import FormfieldView, LeadsView, get_employee,WebEnquiry,lead_assign

urlpatterns = [
    path('formfield/', FormfieldView.as_view(), name='formfield'),
    path("leads/", LeadsView.as_view(), name="leads"),
    path("webenquiry/", WebEnquiry.as_view(), name="webenquiry"),
    
    path("get-employee/", get_employee, name="get-employee"),
    path('lead-assign/', lead_assign, name='lead-assign'),
]

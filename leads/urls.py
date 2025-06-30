from django.urls import path
from .views import FormfieldView, LeadsView, get_employee, WebEnquiry, lead_assign, lead_overview, status_update,convert_to,LeadNotesView,DealView,sales_pipeline,get_deal_overview,DealNoteView,get_form_fields

urlpatterns = [
    path('formfield/', FormfieldView.as_view(), name='formfield'),
    path("leads/", LeadsView.as_view(), name="leads"),
    path("webenquiry/", WebEnquiry.as_view(), name="webenquiry"),
    
    path("get-employee/", get_employee, name="get-employee"),
    path('lead-assign/', lead_assign, name='lead-assign'),
    path('lead-overview/', lead_overview, name='lead-overview'),
    path('lead_status/', status_update, name='status-update'),
    path('lead_conversion/', convert_to, name='lead_conversion'),
    path('lead-note/', LeadNotesView.as_view(), name='lead-note'),
    path('deals/', DealView.as_view(), name='deals'),
    path('deal-overview/', get_deal_overview, name='deal-overview'),
    path('deal-note/', DealNoteView.as_view(), name='deal-note'),
    path('sales-pipeline/', sales_pipeline, name='sales-pipeline'),
    path('get-form-fields/', get_form_fields, name='get-form-fields'),
    
    
]   

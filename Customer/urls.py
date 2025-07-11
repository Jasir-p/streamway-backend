from .views import (
    ContactView,
    AccountsView,
    assign_to_contact,
    account_overview,
    AccountCustomisedView,
    AccountsNotesView,
    assign_to_account)
from django.urls import path


urlpatterns = [
    path('contact/', ContactView.as_view(), name='contact'),
    path('accounts/', AccountsView.as_view(), name='accounts'),
    path('contact-assign/',assign_to_contact, name='contact-assign' ),
    path('account-details/',account_overview, name="account-details"),
    path('account-customized/',AccountCustomisedView.as_view(), name="account-customized"),
    path("notes/",AccountsNotesView.as_view(), name='notes'),
    path("assign-to-account/",assign_to_account, name='assign-to-account'),
]

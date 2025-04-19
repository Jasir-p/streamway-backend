from .views import (
    ContactView,
    AccountsView)
from django.urls import path


urlpatterns = [
    path('contact/', ContactView.as_view(), name='contact'),
    path('accounts/', AccountsView.as_view(), name='accounts'),
]

from django.urls import path
from .views import TaskView,TaskDetailView,EmailsView,MeetingView,get_contacts_by_account

urlpatterns = [
    path('tasks/', TaskView.as_view(), name='tasks'),
    path('task-detail/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('tenant-email/', EmailsView.as_view(), name='tenant-email'),
    path('meeting/', MeetingView.as_view(), name='meeting'),
    path('meeting/<int:meeting_id>/', MeetingView.as_view()),
    path('get-contacts-by-account/<int:account_id>/', get_contacts_by_account, name='get-contacts-by-account')
    
]

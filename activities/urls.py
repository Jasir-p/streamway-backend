from django.urls import path
from .views import TaskView,TaskDetailView,EmailsView

urlpatterns = [
    path('tasks/', TaskView.as_view(), name='tasks'),
    path('task-detail/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('tenant-email/', EmailsView.as_view(), name='tenant-email'),
]

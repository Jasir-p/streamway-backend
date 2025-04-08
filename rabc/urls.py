from django.urls import path
from .views import RoleView,PermissionView,RoleAcessPermissionView

urlpatterns = [
    path("role/",RoleView.as_view(),name='roles'),
    path("permission/", PermissionView.as_view(), name='permission'),
    path("roleacess/", RoleAcessPermissionView.as_view(), name="roleacess") 
]

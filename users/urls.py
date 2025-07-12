from django.urls import path
from .views import EmployeeManagment, EmployeeLoginView, TeamManagmentView, TeamMemberView,user_access, MyTokenRefreshView,password_change,password_change_verify,profile_update,forgot_password,forgot_password_verify_otp

urlpatterns = [
    path('employee/', EmployeeManagment.as_view(), name='employee'),
    path('employee_login/', EmployeeLoginView.as_view(),
         name='employee_login'),
    path('team/', TeamManagmentView.as_view(), name="team"),
    path('team_members/', TeamMemberView.as_view(), name="team_members"),
    path('useraccess/', user_access, name="user_access"),
    path('api/token/employee_refresh/', MyTokenRefreshView.as_view(),
         name="refresh_token_employee"),
    path('password/', password_change, name="password_change"),
    path('verfiy_password/', password_change_verify,
         name="password_change_verify"),
    path("profile_update/", profile_update, name="profile_update"),
    path("forgot_password/", forgot_password, name="forgot_password"),
    path("forgot_password_verify_otp/", forgot_password_verify_otp, name="forgot_password_verify_otp"),
]

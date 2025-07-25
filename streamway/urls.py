"""
URL configuration for streamway project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,

)


from django.conf.urls.static import static
urlpatterns = [
    
    
    path('', include('tenant.urls')),
    path('', include('rabc.urls')),
    path('', include("users.urls")),
    path('api/', include("leads.urls")),
    path('api/', include("Customer.urls")),
    path('api/', include("activities.urls")),
    path('', include("billing.urls")),
    path('',include("communications.urls")),
    path('api/',include("admin_panel.urls")),
    path('api/',include("tenant_panel.urls"))

    
    
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
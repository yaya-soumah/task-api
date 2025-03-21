"""
URL configuration for task_project project.

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
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.authtoken.views import  obtain_auth_token
from django.http import HttpResponse
from django.core.management import call_command

schema_view = get_schema_view(
    openapi.Info(
        title="Task Project",
        default_version='v1',
        description="API for managing urgent and regular tasks",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('tasks.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('migrate/', lambda r: call_command('migrate') or HttpResponse('Done')),
    path('createsuperuser/', lambda r: call_command('createsuperuser', interactive=False, username='admin', email='admin@example.com', password='django123') or HttpResponse('Done')),
]


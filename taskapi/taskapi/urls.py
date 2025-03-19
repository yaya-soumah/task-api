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
    path('api/v1/', include('myapp.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('migrate/', lambda r: call_command('migrate') or HttpResponse('Done')),
    path('superuser/', lambda r: call_command('createsuperuser', interactive=False, username='beast', email='beast@example.com', password='django123') or HttpResponse('Done')),
]


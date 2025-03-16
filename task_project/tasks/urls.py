from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('delete/<type>/<int:task_id>/', views.delete_task, name='delete_task'),
    path('api/v1/urgent-tasks/', views.urgent_task_api, name='urgent_task_api'),
    path('api/v1/regular-tasks/', views.regular_task_api, name='regular_task_api'),
    path('api/v1/delete/<task_type>/<int:task_id>/', views.delete_task_api, name='delete_task_api'),
    ]

urlpatterns += [path('api/v1/urgent-tasks/<int:task_id>/progress/', views.task_progress, name='task_progress'),]
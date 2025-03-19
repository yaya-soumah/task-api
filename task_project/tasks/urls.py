from django.urls import path
from . import views

urlpatterns = [
    path('urgent-tasks/', views.urgent_task_api, name='urgent_task_api'),
    path('regular-tasks/', views.regular_task_api, name='regular_task_api'),
    path('delete/<task_type>/<int:task_id>/', views.delete_task_api, name='delete_task_api'),
    path('projects/', views.project_api, name='project_api'),
    ]

urlpatterns += [path('urgent-tasks/<int:task_id>/progress/', views.task_progress, name='task_progress'),]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('delete/<type>/<int:task_id>/', views.delete_task, name='delete_task'),
    path('api/task/', views.task_api, name='task_api'),
    path('api/delete/<type>/<int:task_id>/', views.delete_task_api, name='delete_task_api'),
]
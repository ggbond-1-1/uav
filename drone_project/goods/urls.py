from django.urls import path
from .views import logistics_form, task_log
from . import views
from .views import allocate_drone

urlpatterns = [
    path('form/', logistics_form, name='logistics_form'),
    path('task-log/', task_log, name='task_log'),
    path('allocate/', allocate_drone, name='allocate_drone'),
]
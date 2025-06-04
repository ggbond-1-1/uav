from django.urls import path
from . import views
from .views import AvailableDronesAPI

app_name = 'drones'

urlpatterns = [
    path('list/', views.drone_list, name='list'),
    path('register/', views.drone_register, name='register'),
    path('detail/<int:pk>/', views.drone_detail, name='detail'),
    path('delete/<int:pk>/', views.drone_delete, name='delete'),
    path('detail/', views.drone_detail_default, name='detail_default'),
    path('api/available_drones/', AvailableDronesAPI.as_view(), name='available_drones_api'),
]
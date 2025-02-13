from django.urls import path
from . import views

urlpatterns = [
    # 无人机列表页面
    path('list/', views.drone_list, name='drone_list'),
    # 无人机详情页面，使用 <int:drone_id> 捕获无人机的 ID
    path('detail/<int:drone_id>/', views.drone_detail, name='drone_detail'),
    # 无人机注册页面
    path('register/', views.drone_register, name='drone_register'),
]
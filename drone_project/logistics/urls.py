from django.urls import path
from . import views

urlpatterns = [
    # 物流跟踪列表页面
    path('list/', views.logistics_list, name='logistics_list'),
    # 物流跟踪详情页面，使用 <int:tracking_id> 捕获物流跟踪的 ID
    path('detail/', views.logistics_detail, name='logistics_detail'),
    path('api/plan_path/', views.plan_path, name='plan_path'),
    # 实时位置追踪API
    path('api/update_drone_position/', views.update_drone_position, name='update_drone_position'),
    path('api/get_active_drones/', views.get_active_drones, name='get_active_drones'),
    path('api/clear_old_positions/', views.clear_old_positions, name='clear_old_positions'),
    path('api/assign_task/', views.assign_task),
    path('api/get_csrf/', views.get_csrf, name='get_csrf'),
    path('api/get_all_drones_status/', views.get_all_drones_status, name='get_all_drones_status'),
    path('api/force_update_goods_status/', views.force_update_goods_status, name='force_update_goods_status'),
    path('api/emergency_stop/', views.emergency_stop, name='emergency_stop'),
    # 实时位置追踪页面
    path('real-time-tracking/', views.real_time_tracking, name='real_time_tracking'),

]
from django.urls import path
from . import views

urlpatterns = [
    # 物流跟踪列表页面
    path('list/', views.logistics_list, name='logistics_list'),
    # 物流跟踪详情页面，使用 <int:tracking_id> 捕获物流跟踪的 ID
    path('detail/', views.logistics_detail, name='logistics_detail'),
]
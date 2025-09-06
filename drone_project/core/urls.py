from django.urls import path
from. import views  # 导入views模块

urlpatterns = [
    path('', views.home, name='home'),  # 使用views.home引用
    path('announcements/', views.announcement, name='announcement'),  # 使用views.announcement引用
    path('introduction/', views.introduction, name='introduction'),
    path('policies/', views.policies, name='policies'),
    path('flight-ranking/', views.flight_ranking, name='flight_ranking'),
]
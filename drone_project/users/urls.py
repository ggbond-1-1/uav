from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
app_name = 'users'
urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset, name='password_reset'),
    path('home/', views.home, name='home'),
    path('some_view/', views.some_view, name='some_view'),
    path('manage/', views.manage, name='manage'),
]
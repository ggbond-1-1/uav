from django.shortcuts import render
# drones/views.py
from django.http import HttpResponse

def drone_list(request):
    # 这里可以添加你的逻辑代码
    return HttpResponse("This is the drone list view.")
# drones/views.py
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Drone  # 确保你有一个 Drone 模型

def drone_detail(request, drone_id):
    # 通过 drone_id 获取无人机对象
    drone = get_object_or_404(Drone, id=drone_id)
    # 返回响应
    return HttpResponse(f"This is the detail page for drone with ID: {drone_id}")
# drones/views.py
from django.shortcuts import render, redirect
from .forms import DroneForm  # 确保你有一个表单类

def drone_register(request):
    if request.method == 'POST':
        form = DroneForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('drone_list')  # 重定向到无人机列表页面
    else:
        form = DroneForm()
    return render(request, 'drones/drone_register.html', {'form': form})
# Create your views here.

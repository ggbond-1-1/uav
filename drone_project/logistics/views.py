from django.http import HttpResponse

def logistics_list(request):
    return HttpResponse("This is the logistics list view.")
from django.shortcuts import render, get_object_or_404
from .models import LogisticsTracking

def logistics_detail(request):
    # 通过 tracking_id 获取物流跟踪对象

    return render(request, '12地图页.html')

from django.shortcuts import render
from django.db.models import Sum, F
from drones.models import Drone
from goods.models import Goods
import math

# 函数视图
def home(request):
    return render(request, '10介绍.html')
# Create your views here.
def announcement(request):
    return render(request, '活动公告页.html')
def introduction(request):
    return render(request, '平台介绍页.html')
def policies(request):
    return render(request, '相关政策页.html')

def flight_ranking(request):
    """飞行排行页面 - 显示所有无人机的飞行里程排行"""
    # 获取所有无人机及其执行的任务
    drones_with_distance = []
    
    for drone in Drone.objects.all():
        # 获取该无人机执行的所有任务
        tasks = Goods.objects.filter(drone=drone)
        
        total_distance = 0
        task_count = 0
        
        for task in tasks:
            # 计算单程距离（这里使用简单的欧几里得距离计算）
            # 实际项目中可能需要更复杂的距离计算算法
            try:
                # 假设地址包含坐标信息，这里简化处理
                # 实际项目中应该从地址解析出经纬度坐标
                distance = calculate_distance_from_addresses(
                    task.sender_address, 
                    task.receiver_address
                )
                total_distance += distance
                task_count += 1
            except:
                # 如果无法计算距离，使用默认值
                total_distance += 10.0  # 默认10公里
                task_count += 1
        
        drones_with_distance.append({
            'drone': drone,
            'total_distance': round(total_distance * 2, 2),  # 将公里转换为里（1公里=2里）
            'task_count': task_count,
            'serial_number': drone.serial_number,
            'model': drone.model,
            'owner': drone.owner.username if drone.owner else '未知'
        })
    
    # 按总距离排序（降序）
    drones_with_distance.sort(key=lambda x: x['total_distance'], reverse=True)
    
    # 添加排名
    for i, drone_data in enumerate(drones_with_distance, 1):
        drone_data['rank'] = i
    
    return render(request, 'flight_ranking.html', {
        'drones_ranking': drones_with_distance
    })

def calculate_distance_from_addresses(sender_address, receiver_address):
    """
    从地址计算距离的函数
    这里使用简化的距离计算，实际项目中应该使用地理编码API
    """
    # 简化的距离计算（基于地址长度和字符差异）
    base_distance = 5.0  # 基础距离5公里
    
    # 根据地址长度调整距离
    sender_len = len(sender_address)
    receiver_len = len(receiver_address)
    
    # 简单的距离估算
    distance = base_distance + (abs(sender_len - receiver_len) * 0.5)
    
    # 确保距离在合理范围内（公里）
    return max(1.0, min(100.0, distance))

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    使用Haversine公式计算两点间的距离
    参数：两个点的经纬度坐标
    返回：距离（公里）
    """
    # 将经纬度转换为弧度
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine公式
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # 地球半径（公里）
    r = 6371
    
    return c * r

from django.db import transaction
from drones.models import Drone
from goods.models import Goods


from django.db import transaction
from django.db.models import F

def allocate_goods():
    # 获取待分配的货物（按重量降序）
    pending_goods = Goods.objects.filter(
        status='pending',
        weight__gt=0
    ).order_by('-weight')

    # 获取可用无人机（在库状态，按剩余可承载重量降序排序）
    available_drones = Drone.objects.filter(
        current_status='in_stock',
        max_takeoff_weight__gt=F('current_load')
    ).annotate(
        available_capacity=F('max_takeoff_weight') - F('current_load')
    ).order_by('-available_capacity')

    with transaction.atomic():
        for goods in pending_goods:
            # 查找最佳无人机
            selected_drone = None
            for drone in available_drones:
                # 计算当前无人机的可用容量
                available_capacity = drone.max_takeoff_weight - drone.current_load
                if available_capacity >= goods.weight:
                    selected_drone = drone
                    break

            if selected_drone:
                # 锁定无人机记录
                locked_drone = Drone.objects.select_for_update().get(pk=selected_drone.pk)

                # 二次验证
                available_capacity = locked_drone.max_takeoff_weight - locked_drone.current_load
                if available_capacity >= goods.weight:
                    # 更新无人机状态
                    locked_drone.current_load += goods.weight
                    if locked_drone.current_load > 0:
                        locked_drone.current_status = 'in_flight'
                    locked_drone.save()

                    # 更新货物状态
                    goods.drone = locked_drone
                    goods.status = 'in_transit'
                    goods.save()
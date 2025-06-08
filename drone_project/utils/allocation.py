from drones.models import Drone
from goods.models import Goods
from django.contrib import messages

from django.db import transaction
from django.db.models import F


def allocate_goods(request=None):
    pending_goods = Goods.objects.filter(
        status='pending',
        weight__gt=0
    ).order_by('-weight')

    # 关键：annotate 应在 filter 之前，且不使用 values()，确保返回 Drone 模型实例
    available_drones = Drone.objects.annotate(
        available_capacity=F('max_takeoff_weight') - F('current_load')
    ).filter(
        current_status='in_stock',
        available_capacity__gt=0,
        max_takeoff_weight__gt=F('current_load')
    ).order_by('-available_capacity')

    with transaction.atomic():
        for goods in pending_goods:
            selected_drone = None
            # 直接遍历 Drone 模型实例，访问 available_capacity 注解字段
            for drone in available_drones:
                if drone.available_capacity >= goods.weight:
                    selected_drone = drone
                    break

            if selected_drone:
                # 锁定无人机并获取最新数据
                locked_drone = Drone.objects.select_for_update().get(pk=selected_drone.pk)
                # 二次验证（使用注解字段或重新计算）
                if (locked_drone.max_takeoff_weight - locked_drone.current_load) >= goods.weight:
                    # 更新无人机状态（使用 F() 表达式保证原子性）
                    Drone.objects.filter(pk=locked_drone.pk).update(
                        current_load=F('current_load') + goods.weight,
                        current_status='in_transit'
                    )

                    # 更新货物状态
                    goods.status = 'allocated'
                    goods.drone = locked_drone
                    goods.save()

                    if request:
                        messages.success(request, f"货物 {goods.name} 已成功分配给无人机 {locked_drone.drone_id}")
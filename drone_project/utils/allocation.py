from drones.models import Drone
from goods.models import Goods
from django.contrib import messages
from django.db import transaction
from django.db.models import F

def allocate_goods(goods_id=None, sender_address=None, receiver_address=None):
    """分配货物到无人机，并返回分配结果"""
    allocation_result = {
        'success': False,
        'drone_id': None,
        'sender_address': sender_address,
        'receiver_address': receiver_address
    }
    
    if goods_id:
        try:
            # 获取特定货物
            goods = Goods.objects.get(pk=goods_id)
            # 如果提供了地址参数，更新货物记录
            if sender_address and receiver_address:
                goods.sender_address = sender_address
                goods.receiver_address = receiver_address
                goods.save()
        except Goods.DoesNotExist:
            return allocation_result
    else:
        # 如果未指定货物ID，则处理所有待分配货物
        goods_list = Goods.objects.filter(
            status='pending',
            weight__gt=0
        ).order_by('-weight')
        
        if not goods_list:
            return allocation_result
        
        goods = goods_list.first()
    
    # 获取可用无人机，按剩余容量降序排列
    # 错误逻辑（当前）
    # 修正后
    available_drones = Drone.objects.annotate(
        available_capacity=F('max_takeoff_weight') - F('current_load')
    ).filter(
        current_status='in_stock',
        available_capacity__gte=goods.weight  # 直接筛选能承载货物重量的无人机
    ).order_by('-available_capacity')
    with transaction.atomic():
        selected_drone = None
        # 查找能够承载该货物的无人机
        for drone in available_drones:
            if drone.available_capacity >= goods.weight:
                selected_drone = drone
                break

        if selected_drone:
            # 锁定无人机并获取最新数据
            locked_drone = Drone.objects.select_for_update().get(pk=selected_drone.pk)
            # 二次验证
            if (locked_drone.max_takeoff_weight - locked_drone.current_load) >= goods.weight:
                # 更新无人机状态
                Drone.objects.filter(pk=locked_drone.pk).update(
                    current_load=F('current_load') + goods.weight,
                    current_status='in_flight'
                )

                # 更新货物状态
                goods.status = 'in_transit'
                goods.drone = locked_drone
                goods.save()
                
                # 更新分配结果
                allocation_result['success'] = True
                allocation_result['drone_id'] = locked_drone.id
                allocation_result['drone_serial'] = locked_drone.serial_number
    
    return allocation_result
from django.shortcuts import render, redirect, get_object_or_404
from .models import Goods
from django.contrib.auth.decorators import login_required
from drones.models import Drone
from django.db import transaction
from django.http import JsonResponse
from utils.allocation import allocate_goods
# 新增导入语句
from django.views.decorators.http import require_http_methods, require_POST
from django.core.exceptions import ValidationError
import logging
from django.contrib import messages

logger = logging.getLogger(__name__)

def validate_weight(value):
    if value <= 0:
        raise ValidationError("重量必须大于 0")

def validate_volume(value):
    if value <= 0:
        raise ValidationError("体积必须大于 0")

def logistics_form(request):
    if request.method == 'POST':
        sender = request.POST.get('sender')
        sender_address = request.POST.get('senderAddress')
        sender_phone = request.POST.get('senderPhone')
        item_type = request.POST.get('itemType')
        weight = request.POST.get('weight')
        volume = request.POST.get('volume')
        receiver = request.POST.get('receiver')
        receiver_address = request.POST.get('receiverAddress')
        receiver_phone = request.POST.get('receiverPhone')
        drone_options = request.POST.get('droneOptions')

        Goods.objects.create(
            sender=sender,
            sender_address=sender_address,
            sender_phone=sender_phone,
            item_type=item_type,
            weight=weight,
            volume=volume,
            receiver=receiver,
            receiver_address=receiver_address,
            receiver_phone=receiver_phone,
            drone_options=drone_options
        )

        return redirect('3首页')

    return render(request, '11东西.html')

def task_log(request):
    # 按创建时间排序获取物流信息
    logistics_info_list = Goods.objects.select_related('drone').all().order_by('created_at')
    return render(request, '3首页.html', {'logistics_info_list': logistics_info_list})

# goods/views.py（修正后）
@login_required
@require_POST
def assign_goods(request, drone_pk):
    drone = get_object_or_404(Drone, pk=drone_pk)

    # 权限验证
    if not (request.user.is_superuser or drone.owner == request.user):
        return JsonResponse({"status": "error", "message": "无操作权限"}, status=403)

    # 获取待分配货物（确保重量不超过无人机剩余容量）
    # 关键：计算剩余容量（最大载重 - 当前负载）
    remaining_capacity = drone.max_takeoff_weight - drone.current_load
    goods = Goods.objects.filter(
        status='pending',
        weight__lte=remaining_capacity,  # 货物重量 ≤ 剩余容量
        drone__isnull=True  # 确保货物未分配过无人机
    ).first()

    if not goods:
        return JsonResponse({
            "status": "error", 
            "message": "没有符合条件的待分配货物（可能重量超限或已分配）"
        }, status=404)

    try:
        with transaction.atomic():
            # 1. 更新无人机状态（锁定事务，防止并发问题）
            drone.current_load += goods.weight
            drone.current_status = 'in_flight'
            drone.save()  # 保存无人机状态

            # 2. 关键：关联货物与无人机，并更新货物状态
            goods.drone = drone  # 建立外键关联
            goods.status = 'in_transit'
            goods.save()  # 保存货物状态

            # 验证关联是否成功（调试用）
            goods.refresh_from_db()  # 从数据库刷新最新数据
            if goods.drone is None:
                raise Exception("货物与无人机关联失败")

            return JsonResponse({
                "status": "success",
                "message": f"成功分配货物 {goods.name} 到无人机 {drone.serial_number}",
                "drone_id": drone.id  # 返回无人机ID，确认分配结果
            })
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"分配失败：{str(e)}"}, status=500)

@require_http_methods(["POST"])
def allocate_drone(request):
    try:
        logger.info(f"收到分配请求，表单数据: {request.POST}")
        sender = request.POST.get('sender_name')
        sender_address = request.POST.get('sender_address')
        sender_phone = request.POST.get('sender_phone')
        item_type = request.POST.get('type')
        weight = float(request.POST.get('weight'))
        volume = float(request.POST.get('volume'))
        receiver = request.POST.get('receiver_name')
        receiver_address = request.POST.get('receiver_address')
        receiver_phone = request.POST.get('receiver_phone')

        goods = Goods.objects.create(
            sender=sender,
            sender_address=sender_address,
            sender_phone=sender_phone,
            item_type=item_type,
            weight=weight,
            volume=volume,
            receiver=receiver,
            receiver_address=receiver_address,
            receiver_phone=receiver_phone,
            status='pending'
        )
        logger.info(f"成功创建货物记录，ID: {goods.id}")

        # 执行分配算法
        allocation_result = allocate_goods(
    goods_id=goods.id,  # 传递货物ID
    sender_address=sender_address,
    receiver_address=receiver_address
)
        # 重新获取最新状态
        goods.refresh_from_db()
        if goods.drone:
            # 更新无人机任务分配次数
            drone = goods.drone
            drone.task_count = 0
            drone.task_count += 1
            drone.save()

            if drone.task_count >= 1:
                # 创建警告消息
                message_text = f"无人机 {drone.serial_number} 已被分配任务超过10次,请关注!"
                messages.warning(request, message_text)

            logger.info(f"货物 {goods.id} 成功分配到无人机 {goods.drone.serial_number}")
            print("返回内容:", {
                'status': 'success',
                'drone_info': f"{goods.drone.serial_number} (剩余容量：{goods.drone.remaining_capacity}kg)",
                'sender_address': sender_address,
                'receiver_address': receiver_address,
                'drone_id': goods.drone.id,
                'message': f"货物已成功分配给无人机 {goods.drone.serial_number}，正在跳转到路径规划页面..."
            })
            return JsonResponse({
                'status': 'success',
                'drone_info': f"{goods.drone.serial_number} (剩余容量：{goods.drone.remaining_capacity}kg)",
                'sender_address': sender_address,
                'receiver_address': receiver_address,
                'serial_number': goods.drone.serial_number,
                'message': f"货物已成功分配给无人机 {goods.drone.serial_number}，正在跳转到路径规划页面..."
            })
        else:
            logger.info(f"货物 {goods.id} 分配失败，暂无可用无人机")
            return JsonResponse({'status': 'error', 'message': '暂无可用无人机'})
    except Exception as e:
        logger.error(f"分配过程中出现错误: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})

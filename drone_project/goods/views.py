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
    logistics_info_list = Goods.objects.all().order_by('created_at')
    return render(request, '3首页.html', {'logistics_info_list': logistics_info_list})

@login_required
@require_POST
def assign_goods(request, drone_pk):
    """处理货物分配操作"""
    drone = get_object_or_404(Drone, pk=drone_pk)

    # 权限验证
    if not (request.user.is_superuser or drone.owner == request.user):
        return JsonResponse({"status": "error", "message": "无操作权限"}, status=403)

    # 获取待分配货物（示例逻辑，需根据实际业务调整）
    goods = Goods.objects.filter(
        status='pending',
        weight__lte=drone.remaining_capacity
    ).first()

    if goods:
        try:
            with transaction.atomic():
                # 更新无人机状态
                drone.current_load += goods.weight
                drone.current_status = 'in_flight'
                drone.save()

                # 更新货物状态
                goods.drone = drone
                goods.status = 'in_transit'
                goods.save()

                return JsonResponse({
                    "status": "success",
                    "message": f"成功分配货物 {goods.name} 到无人机 {drone.serial_number}"
                })
        except Drone.DoesNotExist:
            return JsonResponse({"status": "error", "message": "无人机不存在"}, status=500)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "没有符合条件的待分配货物"}, status=404)

logger = logging.getLogger(__name__)

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
        allocate_goods()
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
            return JsonResponse({
                'status': 'success',
                'drone_info': f"{goods.drone.serial_number} (剩余容量：{goods.drone.remaining_capacity}kg)"
            })
        else:
            logger.info(f"货物 {goods.id} 分配失败，暂无可用无人机")
            return JsonResponse({'status': 'error', 'message': '暂无可用无人机'})
    except Exception as e:
        logger.error(f"分配过程中出现错误: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})
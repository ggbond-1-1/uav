from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Drone
from .forms import DroneForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def drone_register(request):
    """处理无人机注册"""
    if request.method == 'POST':
        form = DroneForm(request.POST)
        if form.is_valid():
            drone = form.save(commit=False)
            drone.owner = request.user
            drone.save()
            
            # 检查是否为AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': '无人机注册成功！',
                    'drone_id': drone.id
                })
            else:
                messages.success(request, '无人机注册成功！')
                return redirect('drones:list')
        else:
            # 检查是否为AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': '表单验证失败，请检查输入！',
                    'errors': form.errors
                })
            else:
                messages.error(request, '表单验证失败，请检查输入！')
    else:
        form = DroneForm()
    return render(request, '5注册我的无人机.html', {'form': form})

@login_required
def drone_list(request):
    user = request.user
    if request.user.is_superuser:
        drones = Drone.objects.all()
        return render(request, '8无人机监管（管理员）.html')
    else:
        drones = Drone.objects.filter(owner=request.user)
        # 使用同一个模板，模板内部会根据drones是否存在来显示不同内容
        template = '4无人机注册空页.html'
    return render(request, template, {'drones': drones})

@login_required
def drone_detail(request, pk):
    """显示无人机详情"""
    drone = get_object_or_404(Drone, pk=pk)
    if not (request.user.is_superuser or drone.owner == request.user):
        messages.error(request, '无权查看该无人机')
        return redirect('drones:list')
    return render(request, '7管理我的无人机.html', {'drone': drone})

@login_required
def drone_delete(request, pk):
    """处理删除操作"""
    drone = get_object_or_404(Drone, pk=pk)
    if request.user.is_superuser or drone.owner == request.user:
        drone.delete()
        messages.success(request, '无人机已删除')
    else:
        messages.error(request, '无权执行此操作')
    return redirect('drones:list')

@login_required
def drone_detail_default(request):
    """无参数详情页默认处理"""
    messages.info(request, '请从列表中选择一个无人机查看详情。')
    return redirect('drones:list')


from django.http import JsonResponse
from django.views import View


class AvailableDronesAPI(View):
    def get(self, request):
        drones = Drone.objects.filter(
            current_status='in_stock',
            remaining_capacity__gt=0
        ).order_by('-remaining_capacity')

        drone_list = [{
            "id": drone.id,
            "serial_number": drone.serial_number,
            "remaining_capacity": drone.remaining_capacity,
            "model": drone.model
        } for drone in drones]

        return JsonResponse({"drones": drone_list})
@login_required
def drone_realtime_position(request):
    # 验证用户是否有权限查看该无人机（根据序列号）
    serial = request.GET.get('serial')
    if not serial:
        messages.error(request, '缺少无人机标识')
        return redirect('drones:list')
    
    # 检查无人机是否属于当前用户
    try:
        drone = Drone.objects.get(serial_number=serial)
        if not (request.user.is_superuser or drone.owner == request.user):
            messages.error(request, '无权查看该无人机位置')
            return redirect('drones:list')
    except Drone.DoesNotExist:
        messages.error(request, '无人机不存在')
        return redirect('drones:list')
    
    return render(request, '13无人机实时位置.html')
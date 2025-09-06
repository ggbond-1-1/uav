from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistrationForm, PasswordResetForm
from django.http import JsonResponse
from goods.models import Goods
from .models import CustomUser


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # 哈希密码
            user.is_active = True  # 激活用户
            user.save()
            return JsonResponse({'success': True})
        else:
            error_messages = []
            for field in form:
                for error in field.errors:
                    error_messages.append(f"{field.label}: {error}")
            for error in form.non_field_errors():
                error_messages.append(error)
            error_message_str = '\n'.join(error_messages)
            return JsonResponse({'success': False, 'message': error_message_str})
    else:
        form = RegistrationForm()
    return render(request, '2用户注册.html', {'form': form})


@login_required
def home(request):
    user = request.user
    username = request.user.username

    if user.is_superuser:
        return render(request, '9用户监管（管理员）.html')
    else:
        # 只获取当前用户拥有的无人机执行的任务
        tasks = Goods.objects.filter(
            drone__isnull=False,  # 确保任务已分配无人机
            drone__owner=user  # 只显示当前用户的无人机
        ).exclude(status='pending').order_by('-id')  # 排除待发货状态，按ID倒序排列
        
        # 过滤掉无人机不存在的任务
        valid_tasks = []
        for task in tasks:
            try:
                # 检查无人机是否仍然存在
                if task.drone:
                    # 如果无人机存在，添加到有效任务列表
                    valid_tasks.append(task)
            except:
                # 如果无人机不存在（已被删除），跳过这个任务
                continue
        
        print(f"查询到 {len(valid_tasks)} 条有效记录")
        # 调试：打印每个任务的状态
        for task in valid_tasks:
            print(f"任务 {task.id}: 状态={task.status}, 状态显示={task.get_status_display()}, 无人机={task.drone.serial_number if task.drone else 'None'}")
        
        task_info_list = []
        for index, task in enumerate(valid_tasks, start=1):
            # 获取无人机序列号和ID
            drone_serial = task.drone.serial_number if task.drone else '-'
            drone_id = task.drone.id if task.drone else '-'
            
            # 获取起点和终点地址
            sender_address = task.sender_address if hasattr(task, 'sender_address') else '未知'
            receiver_address = task.receiver_address if hasattr(task, 'receiver_address') else '未知'
            
            task_info = {
                'index': index,
                'scheduled_time': task.created_at.strftime(
                    '%Y-%m-%d %H:%M') if task.created_at else '未知时间',
                'status': task.get_status_display(),
                'drone_model': task.drone.model if task.drone else '未分配',
                # 无人机序列号（用户可见的唯一标识）
                'drone_serial': drone_serial,
                # 起点和终点地址
                'sender_address': sender_address,
                'receiver_address': receiver_address,
            }
            task_info_list.append(task_info)

        return render(request, '3首页.html', {
            'username': username,
            'task_info_list': task_info_list
        })


@login_required
def some_view(request):
    user = request.user

    return render(request, '1登录界面.html')

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.http import JsonResponse
from .forms import RegistrationForm

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': '用户名或密码错误'})
    return render(request, '1登录界面.html')


def logout_view(request):
    logout(request)
    return redirect('users:login')


def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            new_password = form.cleaned_data['new_password']
            
            try:
                user = CustomUser.objects.get(phone_number=phone_number)
                user.set_password(new_password)
                user.save()
                return JsonResponse({'success': True, 'message': '密码重置成功！'})
            except CustomUser.DoesNotExist:
                return JsonResponse({'success': False, 'message': '用户不存在'})
        else:
            error_messages = []
            for field in form:
                for error in field.errors:
                    error_messages.append(f"{field.label}: {error}")
            for error in form.non_field_errors():
                error_messages.append(error)
            error_message_str = '\n'.join(error_messages)
            return JsonResponse({'success': False, 'message': error_message_str})
    else:
        form = PasswordResetForm()
    
    return render(request, 'password_reset.html', {'form': form})


from django.core.exceptions import ObjectDoesNotExist

@login_required
def manage(request):
    user = request.user
    # 直接从用户模型获取电话号码
    phone_number = user.phone_number or ''

    error_message = None
    success_message = None

    if request.method == 'POST':
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        new_password = request.POST.get('password')

        try:
            # 更新用户名
            if username and username != user.username:
                user.username = username

            # 更新电话号码
            if phone and phone != phone_number:
                user.phone_number = phone

            # 更新密码
            if new_password and new_password != '*' * len(user.password):
                user.set_password(new_password)

            user.save()
            success_message = "信息更新成功！"
        except Exception as e:
            error_message = f"更新信息时出现错误: {str(e)}"

    # 生成用星号代替的密码显示
    masked_password = '*' * len(user.password) if user.password else ''

    return render(request, '6个人信息管理.html', {
        'user': user,
        'masked_password': masked_password,
        'phone_number': phone_number,
        'error_message': error_message,
        'success_message': success_message
    })
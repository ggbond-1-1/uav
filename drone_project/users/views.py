from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistrationForm
from django.http import JsonResponse
from goods.models import Goods


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
        # 使用 id 字段排序（通常与创建时间一致）
        tasks = Goods.objects.exclude(status='pending').order_by('-id')
        print(f"查询到 {tasks.count()} 条记录")
        task_info_list = []
        for index, task in enumerate(tasks, start=1):
            task_info = {
                'index': index,
                'scheduled_time': task.scheduled_time.strftime(
                    '%Y-%m-%d %H:%M') if task.scheduled_time else '无计划时间',
                'status': task.get_status_display(),
                'drone_model': task.drone.model if task.drone else '未分配',
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


from django.core.exceptions import ObjectDoesNotExist

@login_required
def manage(request):
    user = request.user
    try:
        phone_number = user.profile.phone_number
    except (AttributeError, ObjectDoesNotExist):
        phone_number = ''

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
            if hasattr(user, 'profile') and phone != phone_number:
                user.profile.phone_number = phone
                user.profile.save()

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
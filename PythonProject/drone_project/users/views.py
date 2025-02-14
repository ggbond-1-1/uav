from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegistrationForm

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def home(request):
    return render(request, 'home.html')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import CustomUser

@login_required
def some_view(request):
    user = request.user
    if user.is_superuser:
        # 管理员逻辑
        return render(request, 'admin_page.html')
    else:
        # 普通用户逻辑
        return render(request, 'user_page.html')
# Create your views here.

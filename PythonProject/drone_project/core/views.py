
from django.shortcuts import render

# 函数视图
def home(request):
    return render(request, '10介绍.html')
# Create your views here.

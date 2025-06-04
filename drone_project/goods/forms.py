# goods/forms.py
from django import forms
from drones.models import Drone  # 假设你有一个 Drone 模型

class DroneForm(forms.ModelForm):
    class Meta:
        model = Drone
        fields = '__all__'  # 或者指定需要的字段
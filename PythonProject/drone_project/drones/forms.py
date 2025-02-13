# drones/forms.py
from django import forms
from .models import Drone

class DroneForm(forms.ModelForm):
    class Meta:
        model = Drone
        fields = '__all__'  # 或者指定具体的字段
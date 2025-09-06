# drones/forms.py
from django import forms
from .models import Drone

class DroneForm(forms.ModelForm):
    class Meta:
        model = Drone
        # 手动指定需要包含的字段（排除 owner 和 total_flight_time）
        fields = [
            'model',
            'manufacturer',
            'serial_number',
            'purchase_date',
            'warranty_expiry',
            'max_takeoff_weight',
            'max_flight_speed',
            'endurance_time',
            'current_status'
        ]
        labels = {
            'model': '型号',
            'manufacturer': '制造商',
            'serial_number': '序列号',
            'purchase_date': '购买日期',
            'warranty_expiry': '保修截止日期',
            'max_takeoff_weight': '最大起飞重量',
            'max_flight_speed': '最大飞行速度',
            'endurance_time': '续航时间',
            'current_status': '当前状态'
        }
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Drone

@receiver(pre_save, sender=Drone)
def validate_drone_load(sender, instance, **kwargs):
    if instance.current_load < 0:
        raise ValueError("无人机负载不能为负数")
    if instance.current_load > instance.max_takeoff_weight:
        raise ValueError(f"超载！无人机 {instance.serial_number} 当前负载 {instance.current_load}kg 超过最大起飞重量 {instance.max_takeoff_weight}kg")
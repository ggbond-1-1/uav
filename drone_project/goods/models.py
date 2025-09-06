from django.db import models
from django.core.validators import MinValueValidator

class Goods(models.Model):
    STATUS_CHOICES = [
        ('pending', '待发货'),
        ('in_transit', '运输中'),
        ('delivered', '已送达'),
        ('issue', '问题件'),
    ]

    # 原模型中的 name 字段保留，可设置默认值
    name = models.CharField(max_length=255, default='未命名货物')
    # 对应 views 中的 item_type
    item_type = models.CharField(max_length=255)
    weight = models.FloatField(validators=[MinValueValidator(0.01, message='重量必须大于0')])
    volume = models.FloatField(validators=[MinValueValidator(0.001, message='体积必须大于0')])
    # 对应 views 中的 sender
    sender = models.CharField(max_length=255)
    sender_address = models.CharField(max_length=255)
    sender_phone = models.CharField(max_length=15)
    # 对应 views 中的 receiver
    receiver = models.CharField(max_length=255)
    receiver_address = models.CharField(max_length=255)
    receiver_phone = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    drone = models.ForeignKey(
        'drones.Drone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_goods'
    )
    scheduled_time = models.DateTimeField(null=True)
    # 原视图中的 drone_options 字段
    drone_options = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时自动设置为当前时间
    updated_at = models.DateTimeField(auto_now=True)      # 每次更新时自动设置为当前时间

    class Meta:
        db_table = 'goods'
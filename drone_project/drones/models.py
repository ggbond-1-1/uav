from django.db import models
from django.core.validators import MinValueValidator
from users.models import CustomUser


class Drone(models.Model):
    STATUS_CHOICES = [
        ('in_stock', '在库'),
        ('in_flight', '飞行中'),
        ('maintenance', '维修中'),
    ]

    model = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=255, unique=True) 
    purchase_date = models.DateField()
    warranty_expiry = models.DateField()
    max_takeoff_weight = models.FloatField(validators=[MinValueValidator(0.01, message='最大起飞重量必须大于0')])
    max_flight_speed = models.FloatField(validators=[MinValueValidator(0.01, message='最大飞行速度必须大于0')])
    flight_time = models.IntegerField(default=0)  # 添加flight_time字段
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_stock')
    total_flight_time = models.IntegerField(default=0)
    current_load = models.FloatField(default=0)  # 新增当前负载字段
    return_time = models.DateTimeField(null=True, blank=True)
    endurance_time = models.IntegerField(validators=[MinValueValidator(1, message='续航时间必须大于0')], default=1) 
    task_count = models.IntegerField(default=0)
    def __str__(self):
        return self.serial_number

    @property
    def remaining_capacity(self):
        return self.max_takeoff_weight - self.current_load

    def can_accept_goods(self, goods):
        return (
                self.current_status == 'in_stock' and
                self.remaining_capacity >= goods.weight and
                (self.current_load + goods.weight) <= self.max_takeoff_weight
        )

    class Meta:
        db_table = 'drone'


class FlightRecord(models.Model):
    flight_id = models.AutoField(primary_key=True)
    drone = models.ForeignKey(Drone, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    flight_date = models.DateTimeField()
    takeoff_location = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    emergency_record = models.TextField(blank=True)
    goods = models.ForeignKey('goods.Goods', on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'flight records'

class DronePosition(models.Model):
    """无人机实时位置记录模型"""
    drone = models.ForeignKey(Drone, on_delete=models.CASCADE, related_name='positions')
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    task_id = models.CharField(max_length=100, null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = 'drone_position'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.drone.serial_number} - {self.timestamp}"
# Create your models here.

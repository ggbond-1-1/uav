# logistics/models.py
from django.db import models
from drones.models import Drone
from goods.models import Goods

class LogisticsTracking(models.Model):
    tracking_id = models.AutoField(primary_key=True)
    good = models.ForeignKey(Goods, on_delete=models.CASCADE)
    drone = models.ForeignKey(Drone, on_delete=models.CASCADE)
    current_location = models.TextField()  # 替换原数据库中的 geometry 类型
    flight_height = models.IntegerField()
    flight_speed = models.FloatField()
    battery_remain = models.FloatField()
    exception_record = models.TextField()

    class Meta:
        db_table = 'logistics_tracking'

# Create your models here.

from django.db import models
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
    max_takeoff_weight = models.FloatField()
    max_flight_speed = models.FloatField()
    flight_time = models.IntegerField()
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_stock')
    total_flight_time = models.IntegerField(default=0)

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

    class Meta:
        db_table = 'flight records'
# Create your models here.

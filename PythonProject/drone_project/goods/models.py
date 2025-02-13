from django.db import models


class Goods(models.Model):
    STATUS_CHOICES = [
        ('pending', '待发货'),
        ('in_transit', '运输中'),
        ('delivered', '已送达'),
        ('issue', '问题件'),
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    weight = models.FloatField()
    volume = models.FloatField()
    sender_name = models.CharField(max_length=255)
    sender_phone = models.CharField(max_length=15)
    sender_address = models.CharField(max_length=255)
    receiver_name = models.CharField(max_length=255)
    receiver_phone = models.CharField(max_length=15)
    receiver_address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'goods'
# Create your models here.

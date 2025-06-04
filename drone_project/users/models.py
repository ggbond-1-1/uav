from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # 添加自定义字段（如果有）
    phone_number = models.CharField(max_length=15, unique=True, null=True)

    # 为 groups 和 user_permissions 添加 related_name 参数
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='customuser_set',  # 添加 related_name 参数
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',  # 添加 related_name 参数
        related_query_name='customuser',
    )
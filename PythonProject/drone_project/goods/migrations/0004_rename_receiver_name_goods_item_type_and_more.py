# Generated by Django 5.1.5 on 2025-03-24 15:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0003_goods_drone_options_alter_goods_name_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='goods',
            old_name='receiver_name',
            new_name='item_type',
        ),
        migrations.RenameField(
            model_name='goods',
            old_name='sender_name',
            new_name='receiver',
        ),
        migrations.RenameField(
            model_name='goods',
            old_name='type',
            new_name='sender',
        ),
    ]

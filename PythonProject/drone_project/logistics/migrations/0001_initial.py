# Generated by Django 5.1.5 on 2025-02-12 14:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('drones', '0001_initial'),
        ('goods', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LogisticsTracking',
            fields=[
                ('tracking_id', models.AutoField(primary_key=True, serialize=False)),
                ('current_location', models.TextField()),
                ('flight_height', models.IntegerField()),
                ('flight_speed', models.FloatField()),
                ('battery_remain', models.FloatField()),
                ('exception_record', models.TextField()),
                ('drone', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='drones.drone')),
                ('good', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='goods.goods')),
            ],
            options={
                'db_table': 'logistics_tracking',
            },
        ),
    ]

# Generated by Django 2.2.8 on 2021-12-17 10:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("opcua", "0002_add_device_protocol"),
    ]

    operations = [
        migrations.AlterField(
            model_name="opcuadevice",
            name="instrument_handler",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="pyscada.DeviceHandler",
            ),
        ),
    ]

# Generated by Django 2.2.8 on 2021-12-17 14:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("opcua", "0005_auto_20211217_1046"),
    ]

    operations = [
        migrations.AlterField(
            model_name="opcuadevice",
            name="remote_devices_objects",
            field=models.CharField(
                blank=True,
                default="",
                help_text="After creating a remote device, refresh the page until you see the result",
                max_length=5000,
                null=True,
            ),
        ),
    ]

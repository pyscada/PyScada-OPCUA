# Generated by Django 3.2 on 2023-02-10 13:15

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("opcua", "0010_devicehandler_migration"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="opcuadevice",
            name="instrument_handler",
        ),
    ]

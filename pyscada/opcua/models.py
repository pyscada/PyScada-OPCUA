# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyscada.models import Device, DeviceHandler
from pyscada.models import Variable
from . import PROTOCOL_ID

import asyncua

from django.db import models
from django.forms.models import BaseInlineFormSet
from django import forms

import logging

logger = logging.getLogger(__name__)


class OPCUADevice(models.Model):
    opcua_device = models.OneToOneField(
        Device, null=True, blank=True, on_delete=models.CASCADE
    )
    protocol_choices = ((0, "tcp"),)
    protocol = models.PositiveSmallIntegerField(default=0, choices=protocol_choices)
    IP_address = models.GenericIPAddressField(help_text="Example: 192.168.0.234")
    port = models.PositiveSmallIntegerField(default=4840)
    path = models.CharField(
        default="/", max_length=254, help_text="Example: /hbk/clipx"
    )
    user = models.CharField(default="user", null=True, blank=True, max_length=254)
    password = models.CharField(
        default="password", null=True, blank=True, max_length=254
    )

    remote_devices_objects = models.CharField(
        default="",
        max_length=5000,
        blank=True,
        null=True,
        help_text="After creating a remote device, "
        "refresh the page until you see the result",
    )

    protocol_id = PROTOCOL_ID

    def parent_device(self):
        try:
            return self.opcua_device
        except:
            return None

    def __str__(self):
        return self.opcua_device.short_name

    class FormSet(BaseInlineFormSet):
        def add_fields(self, form, index):
            super().add_fields(form, index)
            form.fields["remote_devices_objects"].widget = forms.Textarea()
            form.fields["remote_devices_objects"].disabled = True


class OPCUAVariable(models.Model):
    opcua_variable = models.OneToOneField(
        Variable, null=True, blank=True, on_delete=models.CASCADE
    )
    NamespaceIndex = models.PositiveSmallIntegerField(
        default=0, help_text='"ns" value used in asyncua library'
    )
    Identifier = models.PositiveSmallIntegerField(
        default=0, help_text='"i" value used in asyncua library'
    )

    protocol_id = PROTOCOL_ID

    def __str__(self):
        return self.id.__str__() + "-" + self.opcua_variable.name


class OPCUAMethodArgument(models.Model):
    opcua_method = models.ForeignKey(
        OPCUAVariable, null=True, blank=True, on_delete=models.CASCADE
    )
    position = models.PositiveSmallIntegerField(
        default=0, help_text="Position in call method"
    )
    data_type_choices = ((0, "Default"), (1, "Use variable value class"))
    data_type = models.PositiveSmallIntegerField(
        choices=data_type_choices,
        help_text="Default: use the DataType send by the device<br>"
        "Variable value class: use the value class defined above",
    )
    value = models.CharField(
        default="", max_length=254, blank=True, help_text="Enter a decimal value"
    )


class ExtendedOPCUADevice(Device):
    class Meta:
        proxy = True
        verbose_name = "OPCUA Device"
        verbose_name_plural = "OPCUA Devices"


class ExtendedOPCUAVariable(Variable):
    class Meta:
        proxy = True
        verbose_name = "OPCUA Variable"
        verbose_name_plural = "OPCUA Variables"

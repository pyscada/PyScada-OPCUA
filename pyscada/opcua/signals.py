# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyscada.models import Device, Variable
from pyscada.opcua.models import (
    OPCUADevice,
    OPCUAVariable,
    ExtendedOPCUAVariable,
    ExtendedOPCUADevice,
)

from django.dispatch import receiver
from django.db.models.signals import post_save

import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=OPCUADevice)
@receiver(post_save, sender=OPCUAVariable)
@receiver(post_save, sender=ExtendedOPCUAVariable)
@receiver(post_save, sender=ExtendedOPCUADevice)
def _reinit_daq_daemons(sender, instance, **kwargs):
    """
    update the daq daemon configuration when changes be applied in the models
    """
    if type(instance) is OPCUADevice:
        post_save.send_robust(sender=Device, instance=instance.opcua_device)
    elif type(instance) is OPCUAVariable:
        post_save.send_robust(sender=Variable, instance=instance.opcua_variable)
    elif type(instance) is ExtendedOPCUAVariable:
        post_save.send_robust(
            sender=Variable, instance=Variable.objects.get(pk=instance.pk)
        )
    elif type(instance) is ExtendedOPCUADevice:
        post_save.send_robust(
            sender=Device, instance=Device.objects.get(pk=instance.pk)
        )

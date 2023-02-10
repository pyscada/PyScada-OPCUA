# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from time import time, sleep
from pyscada.device import GenericDevice
from .devices import GenericDevice as GenericHandlerDevice

import sys

import logging

logger = logging.getLogger(__name__)

try:
    import asyncua
    driver_ok = True
except ImportError:
    logger.info('Cannot import smbus')
    driver_ok = False


class Device(GenericDevice):
    """
    OPC-UA device
    """

    def __init__(self, device):
        self.driver_ok = driver_ok
        self.handler_class = GenericHandlerDevice
        super().__init__(device)

        for var in self.device.variable_set.filter(active=1):
            if not hasattr(var, 'opcuavariable'):
                continue
            self.variables[var.pk] = var

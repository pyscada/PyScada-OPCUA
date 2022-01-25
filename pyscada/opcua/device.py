# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from time import time, sleep
from pyscada.opcua.devices import GenericDevice

import sys

import logging

try:
    import asyncua
    driver_opcua_ok = True
except ImportError:
    driver_opcua_ok = False

logger = logging.getLogger(__name__)
_debug = 1


class Device:
    """
    OPC-UA device
    """

    def __init__(self, device):
        self.variables = {}
        self.device = device

        if self.device.opcuadevice.instrument_handler is not None \
                and self.device.opcuadevice.instrument_handler.handler_path is not None:
            sys.path.append(self.device.opcuadevice.instrument_handler.handler_path)
            try:
                mod = __import__(self.device.opcuadevice.instrument_handler.handler_class, fromlist=['Handler'])
                device_handler = getattr(mod, 'Handler')
                self._h = device_handler(self.device, self.variables)
                self.driver_handler_ok = True
            except ImportError:
                self.driver_handler_ok = False
                logger.error("Handler import error : %s" % self.device.short_name)
        else:
            logger.debug("No handler for OPC-UA device : %s" % str(self.device))
            self._h = GenericDevice(self.device, self.variables)
            self.driver_handler_ok = True

        #if driver_opcua_ok and self.driver_handler_ok:
        #    if not self._h.connect():
        #        sleep(60)
        #        self._h.connect()

        for var in self.device.variable_set.filter(active=1):
            if not hasattr(var, 'opcuavariable'):
                continue
            self.variables[var.pk] = var

    def request_data(self):
        output = []

        if not driver_opcua_ok:
            logger.info('Cannot import asyncua')
            return output

        #for item in self.variables.values():
        #    if hasattr(self, '_h'):
        #        value = self._h.read_data(item)
        #    else:
        #        value = None
        #    if value is not None and item.update_value(value, time()):
        #        output.append(item.create_recorded_data_element())

        output = self._h.read_all_data(self.variables)

        return output

    def write_data(self, variable_id, value, task):
        """
        write value to a OPC-UA Device
        """

        output = []
        if not driver_opcua_ok:
            logger.info("Cannot import asyncua")
            return output

        for item in self.variables.values():
            if item.id == variable_id:
                if not item.writeable:
                    return False
                if hasattr(self, '_h'):
                    read_value = self._h.write_data(variable_id, value, task)
                else:
                    read_value = None
                if read_value is not None and item.update_value(read_value, time()):
                    output.append(item.create_recorded_data_element())

        return output
